# twitter-check

A practical toolkit for Twitter/X data exploration that uses browser network requests instead of paid API access. Currently features tools to scrape community members and check follower relationships, perfect for researchers and community managers working with limited resources.

## Features

- Scrapes member information from Twitter/X communities
- Tracks progress with visual progress bar and percentage completion
- Provides estimated time to completion (ETA)
- Handles pagination automatically with cursor tracking
- Detects and handles rate limiting with automatic retries
- Prevents duplicate entries in the output file
- Saves detailed user data to CSV for further analysis
- Logs raw JSON responses with timestamps for debugging and data archiving
- Can resume scraping from where it last stopped using cursor tracking
- Provides performance statistics and summary information

## Prerequisites

- Python 3.6+ (3.8+ recommended)
- Required packages: see `requirements.txt`

## Comprehensive Setup Guide

### Setting up with pyenv (recommended for macOS/Linux)

[pyenv](https://github.com/pyenv/pyenv) allows you to easily switch between Python versions and create isolated environments. Here's how to set it up:

1. **Install pyenv** (if not already installed):

   - On macOS (using Homebrew):
     ```bash
     # Install both pyenv and pyenv-virtualenv
     brew install pyenv
     brew install pyenv-virtualenv
     ```

   - On Linux:
     ```bash
     curl https://pyenv.run | bash
     
     # Add to your shell configuration file (.bashrc, .zshrc, etc.)
     echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc
     echo 'eval "$(pyenv init -)"' >> ~/.bashrc
     echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc
     ```

   - On Windows:
     Windows users should use the built-in `venv` module (see alternative method below)

   > **Note for macOS users**: When installing with Homebrew, shell configuration is typically not required as Homebrew handles the necessary PATH setup. If you experience issues with pyenv functionality, you might need to add initialization commands to your shell configuration (see Linux instructions).

2. **Create and activate a Python environment** (macOS/Linux):
   ```bash
   # Install your preferred Python version (preferrably 3.6+)
   pyenv install 3.11.0
   
   # Create a virtual environment for this project
   pyenv virtualenv 3.11.0 twitter-check
   
   # Activate the environment for this directory
   pyenv local twitter-check
   ```
   
   This will create a `.python-version` file in your project directory that automatically activates the environment when you enter the directory.

### Alternative: Using standard venv (Recommended for Windows)

This is the standard approach using Python's built-in virtual environment module:

1. **Ensure you have Python installed**:
   - Windows: Download from [python.org](https://www.python.org/downloads/) (add Python to PATH during installation)
   - macOS: `brew install python`
   - Linux: `sudo apt install python3` (or your distribution's package manager)

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the environment**:
   - On Windows (Command Prompt):
     ```
     venv\Scripts\activate.bat
     ```
   - On Windows (PowerShell):
     ```
     .\venv\Scripts\Activate.ps1
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```

   You'll know the environment is activated when you see `(venv)` at the beginning of your command prompt.

### Installing Dependencies

Once your virtual environment is activated, install the required packages:

```bash
pip install -r requirements.txt
```

### Setting up Authentication

These scripts require authentication tokens from your Twitter/X browser session:

1. **Log in to Twitter/X** in your browser
2. **Open browser developer tools**:
   - Chrome/Edge: Press F12 or right-click > Inspect > Application tab
   - Firefox: Press F12 or right-click > Inspect > Storage tab
   - Safari: Enable developer tools in preferences, then right-click > Inspect Element > Storage tab

3. **Find the required cookies**:
   - Look for `auth_token` and `ct0` in the Cookies section
   - The `auth_token` is your authentication token
   - The `ct0` is your CSRF token

4. **Set up the community ID**:
   - Navigate to the Twitter/X community you want to scrape
   - The URL will look like `https://twitter.com/i/communities/[COMMUNITY_ID]`
   - Copy the `[COMMUNITY_ID]` portion of the URL

### Setting up Environment Variables (Recommended)

The scripts now support environment variables for authentication tokens. This is the recommended approach to avoid hardcoded tokens.

1. **Use the provided `.env` file**:
   - The repository includes a `.env` file that you can edit directly
   - This file is included in `.gitignore` to prevent accidentally committing your credentials

2. **Edit the `.env` file** with your authentication tokens and settings:
   ```
   # Twitter credentials
   TWITTER_AUTH_TOKEN=your_auth_token_here
   TWITTER_CSRF_TOKEN=your_csrf_token_here
   TWITTER_COMMUNITY_ID=your_community_id_here
   
   # Optional settings
   TWITTER_OUTPUT_FILE=twitter_community_members.csv
   TWITTER_LOGS_DIR=twitter_response_logs
   ```

3. **Run the scripts** normally and they will use the environment variables:
   ```bash
   python get_community_members.py
   python check_followers.py --target TwitterUsername
   ```

4. **Override environment variables** with command-line arguments as needed:
   ```bash
   python check_followers.py --target TwitterUsername --auth-token "different_token"
   ```

5. **Note on security**: 
   - Never share your auth tokens or commit them to public repositories
   - If you accidentally expose your tokens, regenerate them by logging out and back in to Twitter

### Available Tools

The twitter-check toolkit includes these tools:

1. **Community Member Scraper** (`get_community_members.py`): 
   - Collects comprehensive data about members in Twitter communities
   - Handles large communities with pagination and resumable sessions

2. **Follower Relationship Checker** (`check_followers.py`):
   - Analyzes which community members follow a target user
   - Perfect for community engagement analysis and outreach planning

### Typical Workflow

The workflow consists of two steps:

1. **Fetch community members** using `get_community_members.py`
2. **Check which members follow a target user** using `check_followers.py`

This two-step process allows you to:
1. First collect all the community members' data (which may take a while for large communities)
2. Then analyze which of those members follow a specific user

## Usage

Basic usage:
```
python get_community_members.py
```

Resume from last position:
```
python get_community_members.py --continue
```

Set a limit on the number of members to retrieve:
```
python get_community_members.py --limit 1000
```

Specify a custom output file:
```
python get_community_members.py --output custom_filename.csv
```

Specify a different community ID (by default, uses the environment variable):
```
python get_community_members.py --community-id 1234567890123456789
```

Skip fetching community info (faster, but won't show progress percentage):
```
python get_community_members.py --skip-info
```

Combine options:
```
python get_community_members.py --continue --limit 500 --output updated_members.csv
```

## Output Files

The script generates the following files:

1. `twitter_community_members.csv` (or your custom filename)
   - Contains all member data
   - Automatically deduplicates entries

2. `twitter_community_members_metadata.json` (or based on your custom filename)
   - Contains metadata like the last cursor, timestamp, progress percentage, etc.
   - Used for resuming scraping sessions

3. Timestamped JSON response logs in the `twitter_response_logs/` directory
   - Format: `community_response_YYYYMMDD_HHMMSS.json`
   - Contains the raw API responses for debugging or further analysis
   - Format: `community_info_YYYYMMDD_HHMMSS.json` for community information

## Fields in the CSV

- `id`: The user's Twitter/X ID
- `username`: The user's handle (screen_name)
- `name`: The user's display name
- `protected`: Whether the account is protected (private)
- `verified`: Whether the account is verified (legacy verification)
- `is_blue_verified`: Whether the account has Twitter/X Blue verification
- `profile_image_url`: URL to the user's profile image
- `community_role`: The user's role in the community (member, moderator, admin)
- `followers_count`: Number of followers
- `following_count`: Number of accounts the user follows
- `statuses_count`: Number of tweets/posts
- `location`: User's location (if provided)
- `created_at`: When the account was created

## Performance Statistics

At the end of each run, the script provides detailed statistics:
- Total members collected
- Total scraping time
- Average collection rate (members per minute)
- Progress percentage toward the total community size
- Estimated time to complete the entire community
- Number of rate limit hits (if any)

## Resuming Scraping Sessions

The script saves the cursor after each run, allowing you to resume scraping from where you left off. Use the `--continue` flag to start from the last saved position.

## Rate Limiting

The script automatically detects rate limiting responses from Twitter/X. When rate limited:
1. It waits for the duration specified by Twitter/X
2. Automatically retries the request
3. Tracks the number of rate limit hits
4. Provides this information in the final summary

## Error Handling

The script includes robust error handling for:
- Network errors with automatic retries
- Timeout errors with automatic retries
- Rate limiting with automatic retries and tracking
- Authentication issues with helpful error messages

# Twitter Follower Checker Tool

The `check_followers.py` script checks which community members do not follow a specified Twitter/X user. It processes the CSV file generated by the community scraper and identifies members who don't follow the target user.

## Features

- Checks all community members against a target Twitter/X user
- Handles pagination through users' following lists
- Detects rate limiting with automatic retries and backoff
- Saves results to CSV for easy analysis
- Logs API responses for debugging
- Handles protected accounts gracefully
- Shows detailed progress during operation
- Supports processing limits for testing or partial runs

## Usage

Basic usage:
```
python check_followers.py --auth-token YOUR_AUTH_TOKEN --csrf-token YOUR_CSRF_TOKEN --target Tectone
```

Process a specific input file:
```
python check_followers.py --auth-token YOUR_AUTH_TOKEN --csrf-token YOUR_CSRF_TOKEN --target Tectone --input my_community.csv
```

Specify a custom output file:
```
python check_followers.py --auth-token YOUR_AUTH_TOKEN --csrf-token YOUR_CSRF_TOKEN --target Tectone --output not_following_results.csv
```

Set a limit on the number of members to process:
```
python check_followers.py --auth-token YOUR_AUTH_TOKEN --csrf-token YOUR_CSRF_TOKEN --target Tectone --limit 50
```

Create separate files for followers and non-followers with just usernames:
```
python check_followers.py --auth-token YOUR_AUTH_TOKEN --csrf-token YOUR_CSRF_TOKEN --target Tectone --separate
```

## Output Files

By default, the script generates a CSV file containing all members and their follow status for the target user. The output filename defaults to `[input]_follows_[target].csv` (e.g., `twitter_community_members_follows_Tectone.csv`).

The output CSV includes:
- `username`: The user's handle (screen_name)
- `follows_target`: Indicates whether the member follows the target user ("Yes", "No", or "Unknown (Protected)" for private accounts)

When using the `--separate` option, the script generates two separate text files:
- `[input]_following_[target].csv`: Simple text file with one username per line, containing users who follow the target
- `[input]_not_following_[target].csv`: Simple text file with one username per line, containing users who don't follow the target

## Authentication

The script requires authentication tokens from your Twitter/X browser session:
- `auth_token`: From the 'auth_token' cookie
- `csrf_token`: From the 'ct0' cookie or x-csrf-token header

To obtain these tokens:
1. Log in to Twitter/X in your browser
2. Open browser developer tools (F12 or right-click > Inspect)
3. Go to the Application/Storage tab
4. Look for Cookies under Storage
5. Find 'auth_token' and 'ct0' values

# Complete Workflow Tutorial

This section provides a step-by-step guide to using the community analysis tools effectively.

## Step 1: Collect Community Members

First, you'll need to collect the members of the Twitter/X community you're interested in:

1. **Prepare your environment**:
   - Ensure you have Python installed and dependencies set up
   - Have your Twitter auth_token and csrf_token ready

2. **Run the community scraper**:
   ```bash
   python get_community_members.py --community-id YOUR_COMMUNITY_ID
   ```
   
   - The script will show a progress box with real-time updates
   - For large communities, this process might take hours or even days due to Twitter's rate limits
   - The script will automatically handle rate limits and resume from where it left off if interrupted

3. **Check the output**:
   - The script will create a CSV file (default: `twitter_community_members.csv`)
   - It will also create a metadata file to allow for resuming the scraping process

4. **If interrupted, resume the process**:
   ```bash
   python get_community_members.py --continue
   ```

## Step 2: Check Who Follows a Target User

Once you have collected the community members, you can check which ones follow a specific Twitter user:

1. **Run the follower checker**:
   ```bash
   python check_followers.py --auth-token YOUR_AUTH_TOKEN --csrf-token YOUR_CSRF_TOKEN --target TwitterUsername
   ```

   - Replace `TwitterUsername` with the Twitter handle of the user you want to check (without the @ symbol)
   - The script will process all members in the CSV file from Step 1

2. **If interrupted, resume the process** (using the new --continue flag):
   ```bash
   python check_followers.py --auth-token YOUR_AUTH_TOKEN --csrf-token YOUR_CSRF_TOKEN --target TwitterUsername --continue
   ```
   
   - This will skip users that were already processed in previous runs

3. **Check the output**:
   - The script will create a CSV file with follow status for each member
   - Default filename: `twitter_community_members_follows_TwitterUsername.csv`

## Step 3: Analyze the Results

After running both scripts, you'll have two main output files:

1. **Community members data** (`twitter_community_members.csv`):
   - Complete information about all community members
   - Useful for demographic analysis, sorting by follower count, etc.

2. **Follow status data** (`twitter_community_members_follows_TwitterUsername.csv`):
   - Shows which community members follow your target user
   - Can be used to identify potential outreach opportunities

You can use these files for:
- Identifying influential community members
- Finding members who don't follow specific accounts
- Analyzing community composition
- Supporting community engagement strategies

## Tips for Large Communities

For communities with thousands of members:

1. **Use the limit option** during initial testing:
   ```bash
   python get_community_members.py --limit 100
   python check_followers.py --target TwitterUsername --limit 50
   ```

2. **Run on a machine that can stay online** for extended periods, like a cloud server or always-on desktop

3. **Set up cron jobs** or scheduled tasks to automatically resume scraping if you need to run over multiple days:
   ```
   0 */6 * * * cd /path/to/twitter-check && /path/to/python get_community_members.py --continue
   ```

4. **Monitor the logs directory** to check for any API changes or errors

## Common Issues and Solutions

### Rate Limiting

All modules handle rate limiting automatically, but excessive requests may lead to temporary blocks. If you encounter persistent rate limiting:

- Try using different auth tokens
- Decrease request frequency by modifying sleep intervals in the code
- Run during off-peak hours

### Authentication Errors

If you see authentication errors:

- Your tokens may have expired - log in to Twitter again and get fresh tokens
- Twitter may have updated their API - check for script updates

### Missing or Incomplete Data

If community data seems incomplete:

- Ensure you're using the correct community ID
- Check if the community is private and if your account has access
- Verify that your auth tokens have sufficient permissions

## About This Project

This project was created to provide a free alternative to Twitter's paid API for basic data collection needs. It works by simulating browser requests rather than using official API endpoints, which makes it:

1. **Free to use** - No API keys or paid subscriptions required
2. **Potentially fragile** - May break if Twitter changes their internal APIs
3. **For educational purposes** - A learning tool for understanding social networks

### Important Notes

- Since this toolkit relies on reverse-engineered endpoints rather than official APIs, it may stop working without warning if Twitter updates their systems
- The scripts include automatic handling for rate limits, but excessive use might still result in temporary IP blocks
- Always use responsibly and respect Twitter's terms of service

## Contributing

Contributions to twitter-check are welcome! If you encounter issues or have improvements, feel free to:

1. Open an issue describing the problem or enhancement
2. Submit a pull request with your changes
3. Share your use cases and findings

## Disclaimer

This toolkit is for educational and research purposes only. It's designed to help researchers and community managers explore Twitter data without the expense of the official API. 

**Important:**
- Use responsibly and respect Twitter's Terms of Service and rate limits
- The developers are not responsible for any misuse or violations of Twitter's terms
- This approach may break at any time if Twitter changes their internal systems
