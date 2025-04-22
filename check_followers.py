#!/usr/bin/env python3
import argparse
import csv
import json
import os
import requests
import time
import datetime
import sys
import re
from colorama import init, Fore, Back, Style
from dotenv import load_dotenv

# Initialize colorama for cross-platform colored terminal output
init(autoreset=True)

# Load environment variables from .env file if it exists
load_dotenv()


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


class TwitterFollowerChecker:
    def __init__(
        self, auth_token=None, csrf_token=None, logs_dir="twitter_response_logs"
    ):
        """
        Initialize the Twitter Follower Checker

        Args:
            auth_token (str): Twitter auth token from browser cookies
            csrf_token (str): Twitter CSRF token from browser cookies
            logs_dir (str): Directory to store response logs
        """
        # Print a fancy banner to start
        print(f"\n{Fore.BLUE}┏{'━' * 61}┓{Style.RESET_ALL}")
        print(
            f"{Fore.BLUE}┃{Style.RESET_ALL}{Fore.CYAN}  ████████╗██╗    ██╗██╗████████╗████████╗███████╗██████╗    {Style.RESET_ALL}{Fore.BLUE}┃{Style.RESET_ALL}"
        )
        print(
            f"{Fore.BLUE}┃{Style.RESET_ALL}{Fore.CYAN}  ╚══██╔══╝██║    ██║██║╚══██╔══╝╚══██╔══╝██╔════╝██╔══██╗   {Style.RESET_ALL}{Fore.BLUE}┃{Style.RESET_ALL}"
        )
        print(
            f"{Fore.BLUE}┃{Style.RESET_ALL}{Fore.CYAN}     ██║   ██║ █╗ ██║██║   ██║      ██║   █████╗  ██████╔╝   {Style.RESET_ALL}{Fore.BLUE}┃{Style.RESET_ALL}"
        )
        print(
            f"{Fore.BLUE}┃{Style.RESET_ALL}{Fore.CYAN}     ██║   ██║███╗██║██║   ██║      ██║   ██╔══╝  ██╔══██╗   {Style.RESET_ALL}{Fore.BLUE}┃{Style.RESET_ALL}"
        )
        print(
            f"{Fore.BLUE}┃{Style.RESET_ALL}{Fore.CYAN}     ██║   ╚███╔███╔╝██║   ██║      ██║   ███████╗██║  ██║   {Style.RESET_ALL}{Fore.BLUE}┃{Style.RESET_ALL}"
        )
        print(
            f"{Fore.BLUE}┃{Style.RESET_ALL}{Fore.CYAN}     ╚═╝    ╚══╝╚══╝ ╚═╝   ╚═╝      ╚═╝   ╚══════╝╚═╝  ╚═╝   {Style.RESET_ALL}{Fore.BLUE}┃{Style.RESET_ALL}"
        )
        print(f"{Fore.BLUE}┃{Style.RESET_ALL}{' ' * 61}{Fore.BLUE}┃{Style.RESET_ALL}")
        print(
            f"{Fore.BLUE}┃{Style.RESET_ALL}{Fore.WHITE}          F O L L O W E R   C H E C K E R   T O O L          {Style.RESET_ALL}{Fore.BLUE}┃{Style.RESET_ALL}"
        )
        print(f"{Fore.BLUE}┗{'━' * 61}┛{Style.RESET_ALL}\n")

        # Default auth tokens if not provided
        self.auth_token = auth_token or os.getenv("TWITTER_AUTH_TOKEN", "")
        self.csrf_token = csrf_token or os.getenv("TWITTER_CSRF_TOKEN", "")
        self.logs_dir = logs_dir
        self.following_api_url = (
            "https://x.com/i/api/graphql/zx6e-TLzRkeDO_a7p4b3JQ/Following"
        )

        # Create logs directory if it doesn't exist
        os.makedirs(logs_dir, exist_ok=True)

        # Headers needed for the requests
        self.headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "authorization": f"Bearer {os.getenv('TWITTER_BEARER_TOKEN', '')}",
            "content-type": "application/json",
            "x-csrf-token": self.csrf_token,
            "x-twitter-active-user": "yes",
            "x-twitter-auth-type": "OAuth2Session",
            "x-twitter-client-language": "en",
        }

        # Cookies needed for the requests
        self.cookies = {"auth_token": self.auth_token, "ct0": self.csrf_token}

        # Rate limiting tracker
        self.rate_limit_hits = 0

    def check_if_following(self, user_id, target_username):
        """
        Check if a user follows a target account

        Args:
            user_id (str): Twitter user ID to check followings for
            target_username (str): Username we're checking if they follow

        Returns:
            bool: True if following, False if not following, None if error
        """

        # Simplified approach using a single request
        # Set up the parameters for the API call
        variables = {
            "userId": user_id,
            "count": 100,  # Fetch more to increase chance of finding target without pagination
            "includePromotedContent": False,
        }

        params = {
            "variables": json.dumps(variables),
            "features": json.dumps(
                {
                    "rweb_video_screen_enabled": False,
                    "profile_label_improvements_pcf_label_in_post_enabled": True,
                    "rweb_tipjar_consumption_enabled": True,
                    "verified_phone_label_enabled": False,
                    "creator_subscriptions_tweet_preview_api_enabled": True,
                    "responsive_web_graphql_timeline_navigation_enabled": True,
                    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
                    "premium_content_api_read_enabled": False,
                    "communities_web_enable_tweet_community_results_fetch": True,
                    "c9s_tweet_anatomy_moderator_badge_enabled": True,
                    "responsive_web_grok_analyze_button_fetch_trends_enabled": False,
                    "responsive_web_grok_analyze_post_followups_enabled": True,
                    "responsive_web_jetfuel_frame": False,
                    "responsive_web_grok_share_attachment_enabled": True,
                    "articles_preview_enabled": True,
                    "responsive_web_edit_tweet_api_enabled": True,
                    "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
                    "view_counts_everywhere_api_enabled": True,
                    "longform_notetweets_consumption_enabled": True,
                    "responsive_web_twitter_article_tweet_consumption_enabled": True,
                    "tweet_awards_web_tipping_enabled": False,
                    "responsive_web_grok_show_grok_translated_post": False,
                    "responsive_web_grok_analysis_button_from_backend": True,
                    "creator_subscriptions_quote_tweet_preview_enabled": False,
                    "freedom_of_speech_not_reach_fetch_enabled": True,
                    "standardized_nudges_misinfo": True,
                    "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
                    "longform_notetweets_rich_text_read_enabled": True,
                    "longform_notetweets_inline_media_enabled": True,
                    "responsive_web_grok_image_annotation_enabled": True,
                    "responsive_web_enhance_cards_enabled": False,
                }
            ),
        }

        # Set up request headers with the referer for the specific user's following page
        headers = self.headers.copy()
        headers["referer"] = f"https://x.com/i/user/{user_id}/following"
        # Also add additional headers from the curl command for completeness
        headers["priority"] = "u=1, i"

        try:
            response = requests.get(
                self.following_api_url,
                headers=headers,
                cookies=self.cookies,
                params=params,
                timeout=30,
            )

            # Handle rate limiting
            if response.status_code == 429:
                self.rate_limit_hits += 1
                wait_time = min(
                    60 * (2**self.rate_limit_hits), 600
                )  # Exponential backoff up to 10 minutes
                print(
                    f"{Back.YELLOW}{Fore.BLACK} RATE LIMIT {Style.RESET_ALL} Waiting {Style.BRIGHT}{wait_time}s{Style.RESET_ALL} before retrying..."
                )
                time.sleep(wait_time)
                return self.check_if_following(user_id, target_username)

            if response.status_code != 200:
                print(
                    f"{Back.RED}{Fore.WHITE} ERROR {Style.RESET_ALL} HTTP {response.status_code} - {response.text[:100]}..."
                )
                print(
                    f"{Fore.YELLOW}ℹ️  If you're seeing authorization errors, you may need to update your auth_token and csrf_token.{Style.RESET_ALL}"
                )
                return None

            data = response.json()

            # Log the raw response
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = (
                f"{self.logs_dir}/following_response_{user_id}_{timestamp}.json"
            )
            with open(log_filename, "w", encoding="utf-8") as log_file:
                json.dump(data, log_file, indent=4)

            # Process the response to check if target_username is in the followings
            try:
                instructions = (
                    data.get("data", {})
                    .get("user", {})
                    .get("result", {})
                    .get("timeline", {})
                    .get("timeline", {})
                    .get("instructions", [])
                )

                for instruction in instructions:
                    if instruction.get("type") == "TimelineAddEntries":
                        entries = instruction.get("entries", [])
                        for entry in entries:
                            # Process only user entries
                            if "user" in entry.get("entryId", ""):
                                content = entry.get("content", {})
                                if content.get("entryType") == "TimelineTimelineItem":
                                    item_content = content.get("itemContent", {})
                                    if item_content.get("itemType") == "TimelineUser":
                                        user_result = item_content.get(
                                            "user_results", {}
                                        ).get("result", {})

                                        if (
                                            user_result
                                            and user_result.get("__typename") == "User"
                                        ):
                                            screen_name = user_result.get(
                                                "legacy", {}
                                            ).get("screen_name", "")
                                            if (
                                                screen_name.lower()
                                                == target_username.lower()
                                            ):
                                                # Remove this log as we'll have a prettier formatted message in the caller
                                                return True

            except Exception as e:
                print(
                    f"{Back.RED}{Fore.WHITE} ERROR {Style.RESET_ALL} Parsing following data: {str(e)}"
                )
                return None

            # If we reach here, we didn't find the target in the user's followings
            # Remove this log as we'll have a prettier formatted message in the caller
            return False

        except requests.exceptions.Timeout:
            print(
                f"{Back.YELLOW}{Fore.BLACK} TIMEOUT {Style.RESET_ALL} Request timed out. Retrying after 10s..."
            )
            time.sleep(10)
            return self.check_if_following(user_id, target_username)

        except requests.exceptions.ConnectionError:
            print(
                f"{Back.YELLOW}{Fore.BLACK} CONNECTION {Style.RESET_ALL} Network error. Retrying after 15s..."
            )
            time.sleep(15)
            return self.check_if_following(user_id, target_username)

        except Exception as e:
            print(f"{Back.RED}{Fore.WHITE} ERROR {Style.RESET_ALL} {str(e)}")
            return None

    def process_community_members(
        self,
        csv_filename,
        target_username,
        limit=None,
        output_file=None,
        separate=False,
        continue_scan=False,
    ):
        """
        Process all community members and check if they follow the target user

        Args:
            csv_filename (str): Filename of the community members CSV
            target_username (str): Username to check if members are following
            limit (int): Optional limit of members to process
            output_file (str): Output file to save results
            separate (bool): Whether to create separate files for followers and non-followers
            continue_scan (bool): Whether to continue from a previous run by skipping already processed users

        Returns:
            tuple: (list of users not following the target, list of users following the target)
        """
        base_name = os.path.splitext(csv_filename)[0]

        if separate:
            # When using separate files, ignore any output_file parameter
            following_output = f"{base_name}_following_{target_username}.csv"
            not_following_output = f"{base_name}_not_following_{target_username}.csv"
        else:
            # When using a single file, use the provided output_file or default
            if not output_file:
                output_file = f"{base_name}_follows_{target_username}.csv"

        # Read community members
        members = []
        try:
            with open(csv_filename, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    members.append(row)
        except Exception as e:
            print(
                f"{Back.RED}{Fore.WHITE} ERROR {Style.RESET_ALL} Reading CSV: {str(e)}"
            )
            return [], []

        total_members = len(members)
        print(
            f"\n{Back.BLUE}{Fore.WHITE} INFO {Style.RESET_ALL} Found {Style.BRIGHT}{total_members}{Style.RESET_ALL} members in {csv_filename}"
        )

        # Apply limit if specified
        if limit and limit < total_members:
            print(
                f"{Back.BLUE}{Fore.WHITE} INFO {Style.RESET_ALL} Processing only the first {Style.BRIGHT}{limit}{Style.RESET_ALL} members"
            )
            members = members[:limit]

        # Set up data structures for results
        not_following = []
        following = []

        # If continue mode is enabled, load already processed users
        processed_usernames = set()
        if continue_scan:
            # Determine which file to check for previously processed users
            if separate:
                following_output = f"{base_name}_following_{target_username}.csv"
                not_following_output = (
                    f"{base_name}_not_following_{target_username}.csv"
                )

                # Try to load from both files
                for output_file_path in [following_output, not_following_output]:
                    if os.path.exists(output_file_path):
                        with open(output_file_path, "r", encoding="utf-8") as f:
                            for line in f:
                                processed_usernames.add(line.strip())
            else:
                # Single output file
                if not output_file:
                    output_file = f"{base_name}_follows_{target_username}.csv"

                if os.path.exists(output_file):
                    with open(output_file, "r", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            processed_usernames.add(row.get("username", "").strip())
                            if row.get("follows_target") == "Yes":
                                following.append(row)
                            else:
                                not_following.append(row)

            # Print info about continuing from previous run
            if processed_usernames:
                print(
                    f"{Back.BLUE}{Fore.WHITE} INFO {Style.RESET_ALL} Continuing from previous run - {Style.BRIGHT}{len(processed_usernames)}{Style.RESET_ALL} users already processed"
                )

        start_time = time.time()

        # Helper function to ensure consistent spacing that we'll use throughout
        def get_padding(content_len, total_width=56):
            """Calculate padding for text within a box

            Args:
                content_len: Length of the visible content (without ANSI color codes)
                total_width: Target width of the box interior (default: 56)

            Returns:
                int: Number of spaces needed as padding
            """
            # Account for the space at the beginning of each line plus the content
            # The -1 is to account for the space already added at beginning of each line
            return max(0, total_width - content_len - 1)

        # Wrapper for calculating padding directly from colored text
        def get_colored_padding(text, total_width=56):
            """Calculate padding for colored text within a box

            Args:
                text: The full text including ANSI color codes
                total_width: Target width of the box interior (default: 56)

            Returns:
                int: Number of spaces needed as padding
            """
            return get_padding(get_visible_length(text), total_width)

        # Special padding function for the summary box which has a different layout
        def summary_padding(content_len):
            """Calculate padding for the summary box

            Args:
                content_len: Length of the visible content (without ANSI color codes)

            Returns:
                int: Number of spaces needed as padding
            """
            # For summary box we need 2 spaces padding (one at beginning, one at end)
            return max(0, 58 - content_len - 2)

        # Function to wrap long text for summary box (mainly for filenames)
        def wrap_text(text, max_width=50):
            """Wrap text to fit within a maximum width

            Args:
                text: Text to wrap
                max_width: Maximum width before wrapping

            Returns:
                str: Text wrapped to maximum width with ... if needed
            """
            if len(text) <= max_width:
                return text
            return text[: max_width - 3] + "..."

        # Initialize progress_stats with a default value
        progress_stats = "No data yet"

        # Counter for actually processed items in this session
        processed_count = 0

        for i, member in enumerate(members, 1):
            username = member.get("username")
            user_id = member.get("id")

            # Skip already processed users if in continue mode
            if continue_scan and username in processed_usernames:
                continue

            # Increment processed count for this session
            processed_count += 1

            # Calculate and display progress stats
            percent_complete = (i - 1) / len(members) * 100
            elapsed = time.time() - start_time
            items_per_second = processed_count / elapsed if elapsed > 0 else 0

            # Display progress box (but not for the first user)
            if i > 1:
                # Clear console screen first to avoid spam
                os.system("clear" if os.name == "posix" else "cls")

                # Define box width consistently for alignment
                box_width = 57

                # Re-print the initial banner
                print(f"\n{Fore.BLUE}┏{'━' * box_width}┓{Style.RESET_ALL}")

                banner_text = "Twitter Follower Checker - Processing"
                banner_padding = get_padding(len(banner_text), box_width)
                print(
                    f"{Fore.BLUE}┃{Style.RESET_ALL} {Fore.CYAN}{banner_text}{Style.RESET_ALL}{' ' * banner_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
                )

                print(f"{Fore.BLUE}┗{'━' * box_width}┛{Style.RESET_ALL}\n")

                # Calculate remaining users to process
                remaining_users = len(members) - (i - 1)
                if continue_scan:
                    # Count how many users still need to be processed (excluding already processed ones)
                    remaining_users = sum(
                        1
                        for m in members[i - 1 :]
                        if m.get("username") not in processed_usernames
                    )

                # Calculate estimated time based on processed items in this session
                # rather than the loop counter which includes skipped items
                remaining = (
                    remaining_users / items_per_second if items_per_second > 0 else 0
                )
                time_remaining = str(datetime.timedelta(seconds=int(remaining)))
                progress_bar = "█" * int(percent_complete / 4) + "░" * (
                    25 - int(percent_complete / 4)
                )

                # Handle target username display
                target_user_text = f"Target: @{target_username}"
                target_padding = get_padding(len(target_user_text), box_width)

                # Calculate time elapsed
                elapsed_time = str(datetime.timedelta(seconds=int(elapsed)))
                elapsed_text = f"Elapsed: {elapsed_time}"
                elapsed_padding = get_padding(len(elapsed_text), box_width)

                # Format progress and ETA with proper padding
                progress_text = f"Progress: [{progress_bar}] {percent_complete:.1f}%"
                progress_padding = get_padding(
                    len(progress_text.replace("\033", "")), box_width
                )

                eta_text = f"ETA: {time_remaining}"
                eta_padding = get_padding(len(eta_text), box_width)

                # Stats text with proper padding - THIS IS THE KEY FIX
                stats_text = f"Stats: {progress_stats}"
                # Use the utility function to get the visible length without ANSI codes
                stats_visible_length = get_visible_length(stats_text)
                stats_padding = get_padding(stats_visible_length, box_width)

                # Current user being processed
                user_text = f"Processing: @{username} ({i}/{len(members)})"
                user_padding = get_padding(len(user_text), box_width)

                print(f"{Fore.BLUE}┌{'─' * box_width}┐{Style.RESET_ALL}")
                print(
                    f"{Fore.BLUE}│{Style.RESET_ALL} {Fore.CYAN}{target_user_text}{Style.RESET_ALL}{' ' * target_padding}{Fore.BLUE}│{Style.RESET_ALL}"
                )
                print(
                    f"{Fore.BLUE}│{Style.RESET_ALL} {Fore.CYAN}{user_text}{Style.RESET_ALL}{' ' * user_padding}{Fore.BLUE}│{Style.RESET_ALL}"
                )
                print(f"{Fore.BLUE}├{'─' * box_width}┤{Style.RESET_ALL}")
                print(
                    f"{Fore.BLUE}│{Style.RESET_ALL} {Fore.CYAN}{progress_text}{Style.RESET_ALL}{' ' * progress_padding}{Fore.BLUE}│{Style.RESET_ALL}"
                )
                print(
                    f"{Fore.BLUE}│{Style.RESET_ALL} {Fore.CYAN}{eta_text}{Style.RESET_ALL}{' ' * eta_padding}{Fore.BLUE}│{Style.RESET_ALL}"
                )
                print(
                    f"{Fore.BLUE}│{Style.RESET_ALL} {Fore.CYAN}{elapsed_text}{Style.RESET_ALL}{' ' * elapsed_padding}{Fore.BLUE}│{Style.RESET_ALL}"
                )
                print(f"{Fore.BLUE}├{'─' * box_width}┤{Style.RESET_ALL}")
                print(
                    f"{Fore.BLUE}│{Style.RESET_ALL} {Fore.CYAN}{stats_text}{Style.RESET_ALL}{' ' * stats_padding}{Fore.BLUE}│{Style.RESET_ALL}"
                )
                print(f"{Fore.BLUE}└{'─' * box_width}┘{Style.RESET_ALL}")

            if not user_id:
                print(
                    f"{Fore.YELLOW}⚠ {Style.BRIGHT}Missing user ID{Style.RESET_ALL} for {Fore.CYAN}@{username}{Style.RESET_ALL}, skipping"
                )
                continue

            # Skip if the member is the target itself
            if username and username.lower() == target_username.lower():
                # We'll update the status in the progress display
                entry = {"username": username, "follows_target": "Self"}
                following.append(entry)
                continue

            # Skip protected accounts (we can't check their followings)
            if member.get("protected") == "True":
                entry = {"username": username, "follows_target": "Unknown (Protected)"}
                not_following.append(entry)
                continue

            # Check if following - but don't print additional messages that clutter the display
            follows = self.check_if_following(user_id, target_username)

            # Store the result and update the appropriate list
            if follows is None:
                entry = {"username": username, "follows_target": "Unknown"}
                not_following.append(entry)
                # Include the status in the progress_stats to show in the progress box
                progress_stats = (
                    f"Last: {Fore.YELLOW}⚠ Unknown{Style.RESET_ALL} @{username}"
                )
            elif follows:
                entry = {"username": username, "follows_target": "Yes"}
                following.append(entry)
                # Include the status in the progress_stats to show in the progress box
                progress_stats = (
                    f"Last: {Fore.GREEN}✓ Following{Style.RESET_ALL} @{username}"
                )
            else:
                entry = {"username": username, "follows_target": "No"}
                not_following.append(entry)
                # Include the status in the progress_stats to show in the progress box
                progress_stats = (
                    f"Last: {Fore.RED}✗ Not Following{Style.RESET_ALL} @{username}"
                )

            # Save progress periodically (every 5 users)
            if i % 5 == 0 or i == len(members):
                if separate:
                    self._save_results(
                        not_following,
                        not_following_output,
                        username_only=True,
                        append_mode=continue_scan,
                    )
                    self._save_results(
                        following,
                        following_output,
                        username_only=True,
                        append_mode=continue_scan,
                    )
                    # This will be shown in the progress bar, no need for a separate print
                    progress_stats = f"{Fore.GREEN}{len(following)}{Style.RESET_ALL} following, {Fore.RED}{len(not_following)}{Style.RESET_ALL} not following"
                else:
                    # Combine both lists for single file output
                    all_results = not_following + following
                    self._save_results(
                        all_results, output_file, append_mode=continue_scan
                    )
                    # This will be shown in the progress bar, no need for a separate print
                    progress_stats = f"{len(all_results)} total ({Fore.GREEN}{len(following)}{Style.RESET_ALL}/{Fore.RED}{len(not_following)}{Style.RESET_ALL})"

            # Add slight delay between users to avoid rate limiting, but don't print this message
            # as it clutters the output - we'll show status in the progress display
            time.sleep(2)  # Calculate execution statistics
        end_time = time.time()
        execution_time = end_time - start_time
        hours, remainder = divmod(execution_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        execution_time_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        items_per_minute = (
            len(members) / (execution_time / 60) if execution_time > 0 else 0
        )

        # Final save
        if separate:
            self._save_results(
                not_following,
                not_following_output,
                username_only=True,
                append_mode=continue_scan,
            )
            self._save_results(
                following,
                following_output,
                username_only=True,
                append_mode=continue_scan,
            )

            # Clear console for the final report
            os.system("clear" if os.name == "posix" else "cls")

            print(
                f"\n{Back.GREEN}{Fore.WHITE} SUCCESS {Style.RESET_ALL} Processing complete!"
            )

            # Show fancy summary box
            summary_width = 58
            print(f"\n{Fore.BLUE}┏{'━' * summary_width}┓{Style.RESET_ALL}")

            title = f"{Fore.WHITE}{Style.BRIGHT}📊SUMMARY REPORT{Style.RESET_ALL}"
            title_padding = summary_padding(get_visible_length("📊SUMMARY REPORT"))
            print(
                f"{Fore.BLUE}┃{Style.RESET_ALL}  {title}{' ' * title_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
            )

            print(f"{Fore.BLUE}┣{'━' * summary_width}┫{Style.RESET_ALL}")

            # Target
            target_content = f"{Fore.CYAN}Target:{Style.RESET_ALL} {Style.BRIGHT}@{target_username}{Style.RESET_ALL}"
            target_padding = summary_padding(
                get_visible_length(f"Target: @{target_username}")
            )
            print(
                f"{Fore.BLUE}┃{Style.RESET_ALL}  {target_content}{' ' * target_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
            )

            # Total members
            total_content = f"{Fore.CYAN}Total members processed:{Style.RESET_ALL} {Style.BRIGHT}{len(members)}{Style.RESET_ALL}"
            total_padding = summary_padding(
                get_visible_length(f"Total members processed: {len(members)}")
            )
            print(
                f"{Fore.BLUE}┃{Style.RESET_ALL}  {total_content}{' ' * total_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
            )

            # Following
            following_stats = f"{Fore.CYAN}Members following:{Style.RESET_ALL} {Fore.GREEN}{Style.BRIGHT}{len(following)}{Style.RESET_ALL}"
            following_padding = summary_padding(
                get_visible_length(f"Members following: {len(following)}")
            )
            print(
                f"{Fore.BLUE}┃{Style.RESET_ALL}  {following_stats}{' ' * following_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
            )

            # Not following
            not_following_stats = f"{Fore.CYAN}Members not following:{Style.RESET_ALL} {Fore.RED}{Style.BRIGHT}{len(not_following)}{Style.RESET_ALL}"
            not_following_padding = summary_padding(
                get_visible_length(f"Members not following: {len(not_following)}")
            )
            print(
                f"{Fore.BLUE}┃{Style.RESET_ALL}  {not_following_stats}{' ' * not_following_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
            )

            # Processing time
            time_content = (
                f"{Fore.CYAN}Processing time:{Style.RESET_ALL} {execution_time_str}"
            )
            time_padding = summary_padding(
                get_visible_length(f"Processing time: {execution_time_str}")
            )
            print(
                f"{Fore.BLUE}┃{Style.RESET_ALL}  {time_content}{' ' * time_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
            )

            # Processing rate
            rate_text = f"{items_per_minute:.1f} members/minute"
            rate_content = f"{Fore.CYAN}Processing rate:{Style.RESET_ALL} {rate_text}"
            rate_padding = summary_padding(
                get_visible_length(f"Processing rate: {rate_text}")
            )
            print(
                f"{Fore.BLUE}┃{Style.RESET_ALL}  {rate_content}{' ' * rate_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
            )

            print(f"{Fore.BLUE}┣{'━' * summary_width}┫{Style.RESET_ALL}")

            # Output files section
            files_title = f"{Fore.WHITE}{Style.BRIGHT}💾OUTPUT FILE{Style.RESET_ALL}"
            files_padding = summary_padding(get_visible_length("💾OUTPUT FILE"))
            print(
                f"{Fore.BLUE}┃{Style.RESET_ALL}  {files_title}{' ' * files_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
            )

            # Following file
            wrapped_following_output = wrap_text(following_output)
            follow_file = f"{Fore.GREEN}➤{Style.RESET_ALL} Following: {Style.BRIGHT}{wrapped_following_output}{Style.RESET_ALL}"
            follow_padding = summary_padding(
                get_visible_length(f"➤ Following: {wrapped_following_output}")
            )
            print(
                f"{Fore.BLUE}┃{Style.RESET_ALL}  {follow_file}{' ' * follow_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
            )

            # Not following file
            wrapped_not_following = wrap_text(not_following_output)
            nofollow_file = f"{Fore.RED}➤{Style.RESET_ALL} Not following: {Style.BRIGHT}{wrapped_not_following}{Style.RESET_ALL}"
            nofollow_padding = summary_padding(
                get_visible_length(f"➤ Not following: {wrapped_not_following}")
            )
            print(
                f"{Fore.BLUE}┃{Style.RESET_ALL}  {nofollow_file}{' ' * nofollow_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
            )

            print(f"{Fore.BLUE}┗{'━' * summary_width}┛{Style.RESET_ALL}")

        else:
            all_results = not_following + following
            self._save_results(all_results, output_file, append_mode=continue_scan)

            # Clear console for the final report
            os.system("clear" if os.name == "posix" else "cls")

            print(
                f"\n{Back.GREEN}{Fore.WHITE} SUCCESS {Style.RESET_ALL} Processing complete!"
            )

            # Show fancy summary box
            summary_width = 58
            print(f"\n{Fore.BLUE}┏{'━' * summary_width}┓{Style.RESET_ALL}")

            title = f"{Fore.WHITE}{Style.BRIGHT}📊SUMMARY REPORT{Style.RESET_ALL}"
            title_padding = summary_padding(get_visible_length("📊SUMMARY REPORT"))
            print(
                f"{Fore.BLUE}┃{Style.RESET_ALL}  {title}{' ' * title_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
            )

            print(f"{Fore.BLUE}┣{'━' * summary_width}┫{Style.RESET_ALL}")

            # Target
            target_content = f"{Fore.CYAN}Target:{Style.RESET_ALL} {Style.BRIGHT}@{target_username}{Style.RESET_ALL}"
            target_padding = summary_padding(
                get_visible_length(f"Target: @{target_username}")
            )
            print(
                f"{Fore.BLUE}┃{Style.RESET_ALL}  {target_content}{' ' * target_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
            )

            # Total members
            total_content = f"{Fore.CYAN}Total members processed:{Style.RESET_ALL} {Style.BRIGHT}{len(members)}{Style.RESET_ALL}"
            total_padding = summary_padding(
                get_visible_length(f"Total members processed: {len(members)}")
            )
            print(
                f"{Fore.BLUE}┃{Style.RESET_ALL}  {total_content}{' ' * total_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
            )

            # Following
            following_stats = f"{Fore.CYAN}Members following:{Style.RESET_ALL} {Fore.GREEN}{Style.BRIGHT}{len(following)}{Style.RESET_ALL}"
            following_padding = summary_padding(
                get_visible_length(f"Members following: {len(following)}")
            )
            print(
                f"{Fore.BLUE}┃{Style.RESET_ALL}  {following_stats}{' ' * following_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
            )

            # Not following
            not_following_stats = f"{Fore.CYAN}Members not following:{Style.RESET_ALL} {Fore.RED}{Style.BRIGHT}{len(not_following)}{Style.RESET_ALL}"
            not_following_padding = summary_padding(
                get_visible_length(f"Members not following: {len(not_following)}")
            )
            print(
                f"{Fore.BLUE}┃{Style.RESET_ALL}  {not_following_stats}{' ' * not_following_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
            )

            # Processing time
            time_content = (
                f"{Fore.CYAN}Processing time:{Style.RESET_ALL} {execution_time_str}"
            )
            time_padding = summary_padding(
                get_visible_length(f"Processing time: {execution_time_str}")
            )
            print(
                f"{Fore.BLUE}┃{Style.RESET_ALL}  {time_content}{' ' * time_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
            )

            # Processing rate
            rate_text = f"{items_per_minute:.1f} members/minute"
            rate_content = f"{Fore.CYAN}Processing rate:{Style.RESET_ALL} {rate_text}"
            rate_padding = summary_padding(
                get_visible_length(f"Processing rate: {rate_text}")
            )
            print(
                f"{Fore.BLUE}┃{Style.RESET_ALL}  {rate_content}{' ' * rate_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
            )

            print(f"{Fore.BLUE}┣{'━' * summary_width}┫{Style.RESET_ALL}")

            # Output file section
            file_title = f"{Fore.WHITE}{Style.BRIGHT}💾OUTPUT FILE{Style.RESET_ALL}"
            file_title_padding = summary_padding(get_visible_length("💾OUTPUT FILE"))
            print(
                f"{Fore.BLUE}┃{Style.RESET_ALL}  {file_title}{' ' * file_title_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
            )

            # Result file
            wrapped_output_file = wrap_text(output_file)
            result_file = f"{Fore.BLUE}➤{Style.RESET_ALL} Results: {Style.BRIGHT}{wrapped_output_file}{Style.RESET_ALL}"
            result_padding = summary_padding(
                get_visible_length(f"➤ Results: {wrapped_output_file}")
            )
            print(
                f"{Fore.BLUE}┃{Style.RESET_ALL}  {result_file}{' ' * result_padding}{Fore.BLUE}┃{Style.RESET_ALL}"
            )

            print(f"{Fore.BLUE}┗{'━' * summary_width}┛{Style.RESET_ALL}")

        return not_following, following

    def _save_results(self, users, output_file, username_only=False, append_mode=False):
        """
        Save the results to a CSV file

        Args:
            users (list): List of users with their following status
            output_file (str): Output filename
            username_only (bool): If True, only output usernames (no header, one username per line)
            append_mode (bool): Whether to append to existing file instead of overwriting
        """
        if not users:
            return

        # Don't write if we're in append mode but the file doesn't exist yet
        file_exists = os.path.exists(output_file)
        if append_mode and not file_exists:
            append_mode = False

        # If in append mode, read existing entries to avoid duplicates
        existing_usernames = set()
        if append_mode and file_exists:
            try:
                if username_only:
                    with open(output_file, "r", encoding="utf-8") as f:
                        for line in f:
                            existing_usernames.add(line.strip())
                else:
                    with open(output_file, "r", encoding="utf-8", newline="") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            existing_usernames.add(row["username"])
            except Exception as e:
                print(
                    f"{Back.YELLOW}{Fore.BLACK} WARNING {Style.RESET_ALL} Error reading existing file: {str(e)}"
                )
                # If we can't read the existing file, we'll continue but might have duplicates

        try:
            if username_only:
                # Simple text file with one username per line
                mode = "a" if append_mode else "w"
                with open(output_file, mode, encoding="utf-8") as f:
                    for user in users:
                        # Only write if username isn't already in the file
                        if (
                            not append_mode
                            or user["username"] not in existing_usernames
                        ):
                            f.write(f"{user['username']}\n")
            else:
                # CSV file with username and follows_target columns
                fieldnames = ["username", "follows_target"]

                # Filter out users that are already in the file to avoid duplicates
                if append_mode:
                    users_to_write = [
                        user
                        for user in users
                        if user["username"] not in existing_usernames
                    ]
                else:
                    users_to_write = users

                mode = "a" if append_mode else "w"
                with open(output_file, mode, newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    if not append_mode or not file_exists:
                        writer.writeheader()
                    writer.writerows(users_to_write)

        except Exception as e:
            print(
                f"{Back.RED}{Fore.WHITE} ERROR {Style.RESET_ALL} Saving results: {str(e)}"
            )


def main():
    # Clear the terminal for a clean start
    os.system("clear" if os.name == "posix" else "cls")

    # Set up command line arguments
    parser = argparse.ArgumentParser(
        description="Check which Twitter community members don't follow a specific user"
    )

    parser.add_argument(
        "--input",
        type=str,
        default=os.getenv("TWITTER_OUTPUT_FILE", "twitter_community_members.csv"),
        help="Input CSV file with community members",
    )
    parser.add_argument(
        "--target",
        type=str,
        required=True,
        help="Target Twitter username to check if members follow (without the @ symbol)",
    )
    parser.add_argument(
        "--limit", type=int, help="Limit the number of members to process"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output CSV file name (default: [input]_not_following_[target].csv)",
    )
    parser.add_argument(
        "--auth-token",
        type=str,
        default=os.getenv("TWITTER_AUTH_TOKEN"),
        help="Twitter auth_token from browser cookies",
    )
    parser.add_argument(
        "--csrf-token",
        type=str,
        default=os.getenv("TWITTER_CSRF_TOKEN"),
        help="Twitter CSRF token (ct0) from browser cookies",
    )
    parser.add_argument(
        "--separate",
        action="store_true",
        help="Create separate files for followers and non-followers with just usernames",
    )
    parser.add_argument(
        "--continue",
        action="store_true",
        dest="continue_scan",
        help="Continue from a previous run by skipping users already processed",
    )

    args = parser.parse_args()

    # Verify auth tokens are provided through CLI or environment variables
    if not args.auth_token or not args.csrf_token:
        print(
            f"{Fore.RED}Error:{Style.RESET_ALL} Twitter authentication tokens not found."
        )
        print(
            "Please provide auth-token and csrf-token using command line arguments or environment variables."
        )
        print(
            f"You can copy the {Fore.CYAN}.env.example{Style.RESET_ALL} file to {Fore.CYAN}.env{Style.RESET_ALL} and fill in your values."
        )
        sys.exit(1)

    # Create checker instance with auth tokens
    checker = TwitterFollowerChecker(args.auth_token, args.csrf_token)

    if not os.path.exists(args.input):
        print(
            f"{Back.RED}{Fore.WHITE} ERROR {Style.RESET_ALL} Input file {Style.BRIGHT}{args.input}{Style.RESET_ALL} does not exist"
        )
        return 1

    # Process members
    checker.process_community_members(
        args.input,
        args.target,
        limit=args.limit,
        output_file=args.output,
        separate=args.separate,
        continue_scan=args.continue_scan,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
