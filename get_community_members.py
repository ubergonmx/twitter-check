import requests
import json
import time
import csv
import sys
import os
import datetime
import re
from colorama import init, Fore, Style
from dotenv import load_dotenv

# Initialize colorama for cross-platform colored terminal output
init(autoreset=True)

# Load environment variables from .env file if it exists
load_dotenv()


class TwitterCommunityScraper:
    def __init__(self, community_id, auth_token, csrf_token, logs_dir="logs"):
        self.community_id = community_id
        self.base_url = "https://x.com/i/api/graphql/V7OdnMvujMPsCctT_daznQ/membersSliceTimeline_Query"
        self.community_info_url = "https://x.com/i/api/graphql/yl50sLRZmPfKAvxW7H_z0g/CommunitiesFetchOneQuery"
        self.headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "authorization": f"Bearer {os.getenv('TWITTER_BEARER_TOKEN', '')}",
            "content-type": "application/json",
            "priority": "u=1, i",
            "referer": f"https://x.com/i/communities/{community_id}/members",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            "x-csrf-token": csrf_token,
            "x-twitter-active-user": "yes",
            "x-twitter-auth-type": "OAuth2Session",
            "x-twitter-client-language": "en",
        }
        self.cookies = {"auth_token": auth_token, "ct0": csrf_token}
        self.members = []
        self.cursor = None
        self.community_info = None
        self.total_members = None
        self.rate_limit_hits = 0
        self.start_time = None
        self.fetch_rates = []
        self.existing_members_count = 0  # Track number of existing members
        self.seen_member_ids = set()  # Track seen member IDs for deduplication
        self.members_saved_count = 0  # Track number of members saved in this session

        # Create logs directory if it doesn't exist
        self.logs_dir = logs_dir
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

    def count_existing_members(self, filename="twitter_community_members.csv"):
        """Count the number of members already in the CSV file and populate the seen_member_ids set"""
        try:
            if os.path.isfile(filename):
                with open(filename, "r", encoding="utf-8", newline="") as file:
                    reader = csv.reader(file)
                    # Skip header row
                    header = next(reader, None)
                    if not header:
                        return 0

                    # Process each row to get both count and IDs
                    count = 0
                    for row in reader:
                        if row and len(row) > 0:  # Make sure we have data
                            count += 1
                            user_id = row[0]  # ID is the first column

                            # Add to our seen set for duplicate checking
                            if user_id:
                                self.seen_member_ids.add(user_id)

                    # Only count if the file has data
                    if count > 0:
                        self.existing_members_count = count
                        print(f"Found {count} existing members in {filename}")
                        print(
                            f"Loaded {len(self.seen_member_ids)} unique member IDs for duplicate checking"
                        )
                        return count
        except Exception as e:
            print(f"Warning: Could not count existing members: {str(e)}")
        return 0

    def fetch_members(
        self, limit=None, start_cursor=None, output_file="twitter_community_members.csv"
    ):
        """Fetch all community members with pagination"""
        count = 0
        next_cursor = start_cursor
        self.start_time = time.time()

        # Count existing members in the CSV file for accurate progress tracking
        self.count_existing_members(output_file)

        # Make sure we have community info for progress tracking
        if self.total_members is None:
            self.fetch_community_info()

        target_count = (
            min(self.total_members, limit)
            if limit and self.total_members
            else limit or self.total_members or "unknown"
        )

        # Display starting message with fancy box
        self._display_progress_box()

        print(
            f"\n{Fore.YELLOW}Starting fetch{Style.RESET_ALL} of community members{' from cursor: ' + start_cursor if start_cursor else ''}..."
        )
        print(f"Target: {Fore.GREEN}{target_count}{Style.RESET_ALL} members")

        while True:
            batch_start_time = time.time()
            members_batch, next_cursor = self._fetch_members_page(next_cursor)
            batch_time = time.time() - batch_start_time

            if not members_batch:
                print(f"\n{Fore.RED}No members found in this batch.{Style.RESET_ALL}")
                break

            # Save the batch to CSV immediately
            saved_count = self.save_batch_to_csv(members_batch, output_file)

            # Keep the members list updated for backward compatibility
            self.members.extend(members_batch)
            count += len(members_batch)

            # Update cursor in metadata after each batch to handle interruptions
            if next_cursor:
                self.update_metadata(output_file, next_cursor)

            # Track fetch rate (members per second)
            time_str = "unknown"
            eta_str = "unknown"

            if batch_time > 0:
                fetch_rate = len(members_batch) / batch_time
                self.fetch_rates.append(fetch_rate)

                # Calculate average rate from last 10 batches
                avg_rate = sum(self.fetch_rates[-10:]) / min(len(self.fetch_rates), 10)

                # Estimate remaining time
                if self.total_members and avg_rate > 0:
                    # Account for existing members when calculating remaining members
                    remaining_members = self.total_members - (
                        self.members_saved_count + self.existing_members_count
                    )
                    estimated_seconds = remaining_members / avg_rate

                    # Format estimated time
                    if estimated_seconds < 60:
                        time_str = f"{estimated_seconds:.0f}s"
                    elif estimated_seconds < 3600:
                        time_str = f"{estimated_seconds/60:.1f}m"
                    else:
                        time_str = f"{estimated_seconds/3600:.1f}h"

                    # Calculate ETA datetime
                    eta = datetime.datetime.now() + datetime.timedelta(
                        seconds=estimated_seconds
                    )
                    eta_str = eta.strftime("%H:%M:%S")

            # Update the progress display with current information
            self._display_progress_box(
                members_batch=members_batch,
                next_cursor=next_cursor,
                saved_count=saved_count,
                batch_time=batch_time,
                avg_rate=avg_rate if "avg_rate" in locals() else None,
                time_str=time_str,
                eta_str=eta_str,
            )

            if not next_cursor:
                print(
                    f"\n{Fore.GREEN}✓ Fetch complete!{Style.RESET_ALL} No more pages to fetch."
                )
                break

            if limit and count >= limit:
                print(
                    f"\n{Fore.GREEN}✓ Fetch complete!{Style.RESET_ALL} Reached limit of {limit} members."
                )
                break

            # Sleep to avoid rate limiting
            time.sleep(1)

        return self.members

    def _fetch_members_page(self, cursor=None):
        """Fetch a single page of community members"""
        params = {
            "variables": json.dumps(
                {"communityId": self.community_id, "cursor": cursor}
            ),
            "features": json.dumps(
                {"responsive_web_graphql_timeline_navigation_enabled": True}
            ),
        }

        try:
            response = requests.get(
                self.base_url,
                headers=self.headers,
                cookies=self.cookies,
                params=params,
                timeout=30,
            )

            # Handle rate limiting
            if response.status_code == 429:
                self.rate_limit_hits += 1
                retry_after = int(response.headers.get("retry-after", 60))
                print(
                    f"🚨 Rate limited! ({self.rate_limit_hits} hits) Waiting for {retry_after} seconds before retrying..."
                )
                time.sleep(retry_after)
                return self._fetch_members_page(cursor)  # Retry after waiting

            if response.status_code != 200:
                print(f"Error: {response.status_code} - {response.text[:200]}")
                print(
                    "If you're seeing authorization errors, you may need to update your auth_token and csrf_token."
                )
                if self.rate_limit_hits > 0:
                    print(
                        f"You've been rate limited {self.rate_limit_hits} times in this session."
                    )
                    print(
                        "Consider lowering your request rate or using a different account."
                    )
                return [], None

            data = response.json()

            # Log the raw response to a timestamped file
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = f"{self.logs_dir}/community_response_{timestamp}.json"
            with open(log_filename, "w", encoding="utf-8") as log_file:
                json.dump(data, log_file, indent=4)

            print(f"Response logged to {log_filename}")

            # Extract member data from the response using the actual structure
            members_data = []
            next_cursor = None

            try:
                # Get members from the items_results array
                items_results = (
                    data.get("data", {})
                    .get("communityResults", {})
                    .get("result", {})
                    .get("members_slice", {})
                    .get("items_results", [])
                )

                for item in items_results:
                    result = item.get("result", {})

                    # Skip non-user items or unavailable users
                    if result.get("__typename") != "User":
                        continue

                    legacy = result.get("legacy", {})

                    member = {
                        "id": result.get("rest_id"),
                        "username": legacy.get("screen_name"),
                        "name": legacy.get("name"),
                        "protected": legacy.get("protected", False),
                        "verified": legacy.get("verified", False),
                        "is_blue_verified": result.get("is_blue_verified", False),
                        "profile_image_url": legacy.get("profile_image_url_https"),
                        "community_role": result.get("community_role"),
                        "followers_count": legacy.get("followers_count", 0),
                        "following_count": legacy.get("friends_count", 0),
                        "statuses_count": legacy.get("statuses_count", 0),
                        "location": legacy.get("location", ""),
                        "created_at": legacy.get("created_at", ""),
                    }

                    members_data.append(member)

                    # Get the next cursor
                next_cursor = (
                    data.get("data", {})
                    .get("communityResults", {})
                    .get("result", {})
                    .get("members_slice", {})
                    .get("slice_info", {})
                    .get("next_cursor")
                )

                # Store the cursor in the class for later use
                self.cursor = next_cursor

            except Exception as e:
                print(f"Error parsing response data: {str(e)}")

            return members_data, next_cursor

        except requests.exceptions.Timeout:
            print("Request timed out. Retrying after a short pause...")
            time.sleep(10)  # Wait 10 seconds before retrying
            return self._fetch_members_page(cursor)  # Retry the same page
        except requests.exceptions.ConnectionError:
            print("Connection error. Retrying after a short pause...")
            time.sleep(15)  # Wait 15 seconds before retrying
            return self._fetch_members_page(cursor)  # Retry the same page
        except Exception as e:
            print(f"Error fetching members: {str(e)}")
            return [], None

    def save_batch_to_csv(
        self, members_batch, filename="twitter_community_members.csv"
    ):
        """Save a batch of members to CSV immediately after fetching"""
        if not members_batch:
            return 0

        try:
            # Filter out members already seen (duplicates)
            new_members = []
            duplicate_count = 0

            for member in members_batch:
                member_id = member.get("id")
                if member_id and member_id not in self.seen_member_ids:
                    new_members.append(member)
                    # Add to seen set to avoid duplicates in future batches
                    self.seen_member_ids.add(member_id)
                else:
                    duplicate_count += 1

            if not new_members:
                if duplicate_count > 0:
                    print(
                        f"Skipped {duplicate_count} duplicate members, nothing new to save"
                    )
                return 0

            # Check if file exists
            file_exists = os.path.isfile(filename)

            # Write to CSV
            with open(
                filename, "a" if file_exists else "w", newline="", encoding="utf-8"
            ) as file:
                # Determine field names - use the first member's keys or a default set
                fieldnames = (
                    list(new_members[0].keys())
                    if new_members
                    else [
                        "id",
                        "username",
                        "name",
                        "protected",
                        "verified",
                        "is_blue_verified",
                        "profile_image_url",
                        "community_role",
                        "followers_count",
                        "following_count",
                        "statuses_count",
                        "location",
                        "created_at",
                    ]
                )

                writer = csv.DictWriter(file, fieldnames=fieldnames)

                # Only write header if this is a new file
                if not file_exists:
                    writer.writeheader()

                # Write non-duplicate members
                writer.writerows(new_members)

            # Update our count of saved members
            self.members_saved_count += len(new_members)

            if duplicate_count > 0:
                print(f"Skipped {duplicate_count} duplicate members")

            return len(new_members)

        except Exception as e:
            print(f"Error saving batch to CSV: {str(e)}")
            return 0

    def update_metadata(
        self, filename="twitter_community_members.csv", next_cursor=None
    ):
        """Update metadata file with the latest cursor and progress info"""
        try:
            # Create a metadata file to store the last cursor and progress info
            progress_percentage = None
            if self.total_members:
                # Include existing members in progress calculation
                total_collected = self.members_saved_count + self.existing_members_count
                progress_percentage = min(
                    total_collected / self.total_members * 100, 100
                )

            metadata = {
                "last_cursor": next_cursor,
                "last_updated": datetime.datetime.now().isoformat(),
                "collected_members": self.members_saved_count,
                "existing_members": self.existing_members_count,
                "total_collected": self.members_saved_count
                + self.existing_members_count,
                "total_members": self.total_members,
                "progress_percentage": progress_percentage,
                "community_id": self.community_id,
            }

            metadata_filename = f"{os.path.splitext(filename)[0]}_metadata.json"
            with open(metadata_filename, "w", encoding="utf-8") as meta_file:
                json.dump(metadata, meta_file, indent=4)

            return True

        except Exception as e:
            print(f"Error updating metadata: {str(e)}")
            return False

    def save_to_csv(self, filename="twitter_community_members.csv", next_cursor=None):
        """Save the collected members to a CSV file (only needed for final metadata update)"""
        # Update the metadata with final cursor
        self.update_metadata(filename, next_cursor)
        print(f"Final metadata saved to {os.path.splitext(filename)[0]}_metadata.json")

    def get_last_cursor(self, filename="twitter_community_members.csv"):
        """Get the last cursor from metadata file"""
        metadata_filename = f"{os.path.splitext(filename)[0]}_metadata.json"

        if os.path.isfile(metadata_filename):
            try:
                with open(metadata_filename, "r", encoding="utf-8") as meta_file:
                    metadata = json.load(meta_file)
                    return metadata.get("last_cursor")
            except Exception as e:
                print(f"Error reading metadata: {str(e)}")

        return None

    def fetch_community_info(self):
        """Fetch community information including member count"""
        try:
            params = {
                "variables": json.dumps(
                    {"communityId": self.community_id, "withDmMuting": False}
                ),
                "features": json.dumps(
                    {
                        "profile_label_improvements_pcf_label_in_post_enabled": True,
                        "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
                        "responsive_web_graphql_timeline_navigation_enabled": True,
                        "rweb_tipjar_consumption_enabled": True,
                        "verified_phone_label_enabled": False,
                    }
                ),
            }

            print(f"Fetching community info for community {self.community_id}...")

            response = requests.get(
                self.community_info_url,
                headers=self.headers,
                cookies=self.cookies,
                params=params,
                timeout=30,
            )

            if response.status_code != 200:
                print(f"Error: {response.status_code} - {response.text}")
                return None

            data = response.json()

            # Log the raw response to a timestamped file
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = f"{self.logs_dir}/community_info_{timestamp}.json"
            with open(log_filename, "w", encoding="utf-8") as log_file:
                json.dump(data, log_file, indent=4)

            print(f"Community info logged to {log_filename}")

            # Extract community data
            community_data = (
                data.get("data", {}).get("communityResults", {}).get("result", {})
            )

            if community_data:
                self.community_info = community_data
                self.total_members = community_data.get("member_count")

                name = community_data.get("name", "Unknown")
                description = community_data.get("description", "No description")
                member_count = self.total_members
                moderator_count = community_data.get("moderator_count", 0)

                print(f"Community: {name}")
                print(f"Description: {description}")
                print(f"Total members: {member_count}")
                print(f"Moderators: {moderator_count}")

                return community_data

            return None

        except Exception as e:
            print(f"Error fetching community info: {str(e)}")
            return None

    def _get_progress_bar(self, percentage, width=25):
        """
        Create a progress bar with given percentage

        Args:
            percentage: Percentage complete (0-100)
            width: Width of the progress bar in characters

        Returns:
            str: Progress bar as string with ANSI colors
        """
        filled = int(width * percentage / 100)
        return f"{Fore.GREEN}{'█' * filled}{Fore.LIGHTBLACK_EX}{'░' * (width - filled)}{Style.RESET_ALL}"

    def _display_progress_box(
        self,
        members_batch=None,
        next_cursor=None,
        saved_count=0,
        batch_time=0,
        avg_rate=None,
        time_str=None,
        eta_str=None,
    ):
        """
        Display a fancy progress box with current status

        Args:
            members_batch: Current batch of members fetched
            next_cursor: Next cursor value
            saved_count: Number of members saved in current batch
            batch_time: Time taken for current batch
            avg_rate: Average fetch rate (members per second)
            time_str: String representation of estimated time
            eta_str: String representation of ETA
        """
        # Clear console screen
        os.system("clear" if os.name == "posix" else "cls")

        # Calculate box width
        box_width = 70

        # Calculate progress
        total_collected = self.members_saved_count + self.existing_members_count
        if self.total_members:
            progress = min(total_collected / self.total_members * 100, 100)
        else:
            progress = 0

        progress_bar = self._get_progress_bar(progress)

        # Helper function for padding
        def get_padding(content_len, width=box_width):
            return max(0, width - content_len - 1)

        # Print header
        print(f"\n{Fore.BLUE}┏{'━' * box_width}┓{Style.RESET_ALL}")

        banner_text = f"Twitter Community Member Scraper"
        banner_visible_text = f"{Fore.CYAN}{banner_text}{Style.RESET_ALL}"
        banner_padding = get_padding(get_visible_length(banner_text))
        print(
            f"{Fore.BLUE}┃{Style.RESET_ALL} {banner_visible_text}{' ' * banner_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
        )

        print(f"{Fore.BLUE}┣{'━' * box_width}┫{Style.RESET_ALL}")

        # Community info
        if self.community_info:
            community_name = self.community_info.get("name", "Unknown")
            community_text = f"Community: {Fore.GREEN}{community_name}{Style.RESET_ALL} (ID: {self.community_id})"
            community_visible_text = (
                f"Community: {community_name} (ID: {self.community_id})"
            )
            community_padding = get_padding(get_visible_length(community_visible_text))
            print(
                f"{Fore.BLUE}┃{Style.RESET_ALL} {community_text}{' ' * community_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
            )
        else:
            community_text = f"Community ID: {self.community_id}"
            community_padding = get_padding(get_visible_length(community_text))
            print(
                f"{Fore.BLUE}┃{Style.RESET_ALL} {community_text}{' ' * community_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
            )

        # Progress information
        print(f"{Fore.BLUE}┣{'━' * box_width}┫{Style.RESET_ALL}")

        # Progress bar
        progress_text = f"Progress: [{progress_bar}] {progress:.1f}%"
        progress_padding = get_padding(get_visible_length(progress_text))
        print(
            f"{Fore.BLUE}┃{Style.RESET_ALL} {progress_text}{' ' * progress_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
        )

        # Counts
        if self.total_members:
            counts_text = (
                f"Members: {Fore.YELLOW}{total_collected}{Style.RESET_ALL}/{Fore.GREEN}{self.total_members}{Style.RESET_ALL} "
                + f"({Fore.CYAN}{self.members_saved_count}{Style.RESET_ALL} new, {Fore.BLUE}{self.existing_members_count}{Style.RESET_ALL} existing)"
            )
            counts_visible_text = f"Members: {total_collected}/{self.total_members} ({self.members_saved_count} new, {self.existing_members_count} existing)"
            counts_padding = get_padding(get_visible_length(counts_visible_text))
            print(
                f"{Fore.BLUE}┃{Style.RESET_ALL} {counts_text}{' ' * counts_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
            )
        else:
            counts_text = (
                f"Members: {Fore.YELLOW}{total_collected}{Style.RESET_ALL} "
                + f"({Fore.CYAN}{self.members_saved_count}{Style.RESET_ALL} new, {Fore.BLUE}{self.existing_members_count}{Style.RESET_ALL} existing)"
            )
            counts_visible_text = f"Members: {total_collected} ({self.members_saved_count} new, {self.existing_members_count} existing)"
            counts_padding = get_padding(get_visible_length(counts_visible_text))
            print(
                f"{Fore.BLUE}┃{Style.RESET_ALL} {counts_text}{' ' * counts_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
            )

        # Current batch info
        if members_batch:
            batch_text = (
                f"Current batch: {len(members_batch)} fetched, {saved_count} saved"
            )
            batch_padding = get_padding(get_visible_length(batch_text))
            print(
                f"{Fore.BLUE}┃{Style.RESET_ALL} {batch_text}{' ' * batch_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
            )

        # Rate and ETA
        if avg_rate and batch_time > 0:
            rate_text = f"Rate: {avg_rate:.1f} members/sec"
            rate_padding = get_padding(get_visible_length(rate_text))
            print(
                f"{Fore.BLUE}┃{Style.RESET_ALL} {rate_text}{' ' * rate_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
            )

            if time_str and eta_str:
                eta_text = f"ETA: {time_str} ({eta_str})"
                eta_padding = get_padding(get_visible_length(eta_text))
                print(
                    f"{Fore.BLUE}┃{Style.RESET_ALL} {eta_text}{' ' * eta_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
                )

        # Cursor info (debugging)
        if next_cursor and len(next_cursor) > 10:
            cursor_text = f"Next cursor: {next_cursor[:10]}..."
            cursor_padding = get_padding(get_visible_length(cursor_text))
            print(
                f"{Fore.BLUE}┃{Style.RESET_ALL} {cursor_text}{' ' * cursor_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
            )

        print(f"{Fore.BLUE}┗{'━' * box_width}┛{Style.RESET_ALL}")
        time.sleep(1)  # Add a short delay to make the progress box readable


# Utility function to strip ANSI color codes and get visible length
def get_visible_length(text):
    """Calculate the visible length of text by removing ANSI color codes

    Args:
        text: Text that may contain ANSI color codes

    Returns:
        int: Length of text as it would appear on screen
    """
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return len(ansi_escape.sub("", text))


def main():
    # Get values from environment variables
    community_id = os.getenv("TWITTER_COMMUNITY_ID")

    # Authentication tokens from environment variables
    auth_token = os.getenv("TWITTER_AUTH_TOKEN")
    csrf_token = os.getenv("TWITTER_CSRF_TOKEN")

    if not auth_token or not csrf_token:
        print(
            f"{Fore.RED}Error:{Style.RESET_ALL} Twitter authentication tokens not found in environment variables."
        )
        print(
            "Please set TWITTER_AUTH_TOKEN and TWITTER_CSRF_TOKEN in your .env file or as environment variables."
        )
        print(
            f"You can copy the {Fore.CYAN}.env.example{Style.RESET_ALL} file to {Fore.CYAN}.env{Style.RESET_ALL} and fill in your values."
        )
        sys.exit(1)

    # Optional parameters with environment variable support
    limit = None  # Set a number to limit the members to fetch, or None for all
    output_file = os.getenv("TWITTER_OUTPUT_FILE", "twitter_community_members.csv")
    logs_dir = os.getenv("TWITTER_LOGS_DIR", "twitter_response_logs")

    # Set up command line arguments
    import argparse

    parser = argparse.ArgumentParser(description="Scrape Twitter community members")
    parser.add_argument(
        "--continue",
        dest="continue_from_last",
        action="store_true",
        help="Continue from last cursor position",
    )
    parser.add_argument(
        "--limit", type=int, help="Limit the number of members to fetch"
    )
    parser.add_argument("--output", type=str, help="Output CSV file name")
    parser.add_argument(
        "--skip-info",
        dest="skip_info",
        action="store_true",
        help="Skip fetching community info (faster but won't show progress percentage)",
    )
    parser.add_argument(
        "--community-id",
        type=str,
        help="Twitter community ID to scrape (overrides default)",
    )
    args = parser.parse_args()

    # Override defaults with command line arguments if provided
    if args.limit:
        limit = args.limit
    if args.output:
        output_file = args.output
    if args.community_id:
        community_id = args.community_id

    print(f"Starting to scrape community {community_id}")
    print(f"Output will be saved to: {output_file}")
    print(f"Response logs will be saved to: {logs_dir}")

    # Create scraper instance
    start_time = time.time()
    scraper = TwitterCommunityScraper(
        community_id, auth_token, csrf_token, logs_dir=logs_dir
    )

    # Get community info first for progress tracking
    if not args.skip_info:
        scraper.fetch_community_info()

    # Get the last cursor if continuing
    start_cursor = None
    if args.continue_from_last:
        start_cursor = scraper.get_last_cursor(output_file)
        if start_cursor:
            print(f"Continuing from cursor: {start_cursor}")
        else:
            print("No saved cursor found. Starting from the beginning.")

    # Fetch members
    scraper.fetch_members(
        limit=limit, start_cursor=start_cursor, output_file=output_file
    )

    # Store the final next_cursor for the metadata
    last_cursor = None
    if scraper.cursor:
        last_cursor = scraper.cursor

    # Final metadata update
    scraper.save_to_csv(output_file, next_cursor=last_cursor)

    total_time = time.time() - start_time
    print(f"\n===== SCRAPING SUMMARY =====")
    print(f"Members collected this session: {scraper.members_saved_count}")
    if scraper.existing_members_count > 0:
        print(f"Existing members in file: {scraper.existing_members_count}")
        print(
            f"Total members across all sessions: {scraper.members_saved_count + scraper.existing_members_count}"
        )
    print(f"Data saved to {output_file}")

    # Calculate statistics
    if total_time > 0:
        members_per_second = scraper.members_saved_count / total_time
        members_per_minute = members_per_second * 60

        # Format time nicely
        if total_time < 60:
            time_str = f"{total_time:.1f} seconds"
        elif total_time < 3600:
            time_str = f"{total_time/60:.1f} minutes"
        else:
            time_str = f"{total_time/3600:.1f} hours"

        print(f"Total time: {time_str}")
        print(f"Average rate: {members_per_minute:.1f} members/minute")

        if scraper.rate_limit_hits > 0:
            print(f"Rate limit hits: {scraper.rate_limit_hits}")

    # Print community information
    if scraper.community_info:
        print("\n===== COMMUNITY INFORMATION =====")
        print(f"  Name: {scraper.community_info.get('name', 'Unknown')}")
        print(
            f"  Description: {scraper.community_info.get('description', 'No description')}"
        )
        print(f"  Member Count: {scraper.total_members}")
        print(f"  Created At: {scraper.community_info.get('created_at')}")

        if scraper.total_members:
            # Include existing members in progress calculation for final summary
            total_collected = (
                scraper.members_saved_count + scraper.existing_members_count
            )
            progress = min(total_collected / scraper.total_members * 100, 100)
            progress_bar = scraper._get_progress_bar(progress)
            print(
                f"  Progress: {progress_bar} {progress:.2f}% ({total_collected}/{scraper.total_members} members)"
            )
            # Show breakdown of existing vs. new members
            if scraper.existing_members_count > 0:
                print(
                    f"    - {scraper.existing_members_count} existing members from previous runs"
                )
                print(
                    f"    - {scraper.members_saved_count} new members from this session"
                )

            # Estimate time to completion for all members
            if members_per_second > 0 and progress < 100:
                # Account for existing members when calculating remaining members
                remaining_members = scraper.total_members - total_collected
                remaining_time = remaining_members / members_per_second

                if remaining_time < 60:
                    remaining_str = f"{remaining_time:.0f} seconds"
                elif remaining_time < 3600:
                    remaining_str = f"{remaining_time/60:.1f} minutes"
                else:
                    remaining_str = f"{remaining_time/3600:.1f} hours"

                print(f"  Estimated time to complete all members: {remaining_str}")
    else:
        print("No community information available.")

    # Also save the final next_cursor (if any) for next run
    if last_cursor:
        print(f"\nLast cursor: {last_cursor}")
        print(
            "You can continue from this cursor in the next run using the --continue flag"
        )


if __name__ == "__main__":
    main()
