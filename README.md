# twitter-check

A practical toolkit for Twitter/X data exploration that uses browser network requests instead of paid API access. Currently features tools to scrape community members and check follower relationships, perfect for researchers and community managers working with limited resources.

## ✨ Features

- Scrapes member information from Twitter/X communities
- Checks which community members follow a specific Twitter/X user
- Visualizes progress with colorful terminal display and ETA
- Handles rate limiting and pagination automatically
- Saves detailed user data for analysis

## 🚀 Quick Start

### 1. Set up your environment

```bash
# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate
# OR (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Get Twitter tokens & create .env file

1. Log in to Twitter/X in your browser
2. Press F12 (or right-click > Inspect)
3. For auth and CSRF tokens:
   - Go to Application tab > Cookies
   - Find and copy `auth_token` and `ct0` cookie values
4. For bearer token:
   - Go to Network tab 
   - Click on any `client_event.json` request
   - In the Headers section, find "Authorization"
   - Copy the token that appears after the word `Bearer`
5. Duplicate the `.env.example` file and rename it to `.env`
6. Fill in your tokens in the `.env` file:

```
# Twitter credentials
TWITTER_AUTH_TOKEN=your_auth_token_from_cookies
TWITTER_CSRF_TOKEN=your_ct0_cookie_value
TWITTER_BEARER_TOKEN=your_bearer_token_copied_from_network_tab
TWITTER_COMMUNITY_ID=your_community_id_from_url

# Optional settings
TWITTER_OUTPUT_FILE=twitter_community_members.csv
TWITTER_LOGS_DIR=twitter_response_logs
```

### 3. Run the tools

**Scrape community members:**
```bash
python get_community_members.py
```

**Check who follows a target user:**
```bash
python check_followers.py --target TwitterUsername
```

## 📋 Tools & Usage

### Community Member Scraper

```bash
# Basic usage
python get_community_members.py

# Resume from last position
python get_community_members.py --continue

# Limit number of members to retrieve
python get_community_members.py --limit 1000

# Custom output file
python get_community_members.py --output custom_filename.csv

# Specify a different community ID
python get_community_members.py --community-id 1234567890123456789

# Skip fetching community info (faster, but won't show progress percentage)
python get_community_members.py --skip-info
```

### Follower Relationship Checker

```bash
# Basic usage
python check_followers.py --target TwitterUsername

# Resume from last position
python check_followers.py --target TwitterUsername --continue

# Process only a limited number of members
python check_followers.py --target TwitterUsername --limit 50

# Create separate files for followers and non-followers (usernames only)
python check_followers.py --target TwitterUsername --separate
```

## 📊 Output Files

**Community Scraper:**
- `twitter_community_members.csv`: All member data
- `twitter_community_members_metadata.json`: Metadata for resuming scraping
- Timestamped JSON logs in `twitter_response_logs` for debugging

**Follower Checker:**
- `twitter_community_members_follows_TwitterUsername.csv`: Follow status for each member
- Or with `--separate` option:
  - `twitter_community_members_following_TwitterUsername.txt`: Users who follow the target
  - `twitter_community_members_not_following_TwitterUsername.txt`: Users who don't follow the target

## 💡 Tips & Troubleshooting

### For Large Communities

- Use the `--limit` option during initial testing
- Run on a machine that can stay online for extended periods
- Set up cron jobs to resume scraping automatically:
  ```
  0 */6 * * * cd /path/to/twitter-check && /path/to/python get_community_members.py --continue
  ```
- Monitor the logs directory for API changes or errors

### Common Issues

**Rate Limiting:**
- The scripts handle this automatically, but you can try different auth tokens
- Run during off-peak hours

**Authentication Errors:**
- Your tokens may have expired - get fresh tokens
- Twitter may have updated their API

**Missing Data:**
- Check if the community is private and your account has access
- Verify your auth tokens have sufficient permissions

## 🛑 Important Notes

- This toolkit uses reverse-engineered endpoints rather than official APIs
- It may stop working if Twitter changes their internal systems
- Always use responsibly and respect Twitter's rate limits and terms of service

## ⚙️ Advanced Options

<details>
<summary>Click to expand additional details and options</summary>

### Available Data Fields

The community member CSV includes:
- `id`: The user's Twitter/X ID
- `username`: The user's handle (screen_name)
- `name`: The user's display name
- `protected`: Whether the account is protected
- `verified`: Whether the account is verified (legacy)
- `is_blue_verified`: Whether the account has Blue verification
- `profile_image_url`: URL to the profile image
- `community_role`: Role in the community (member, moderator, admin)
- `followers_count`: Number of followers
- `following_count`: Number of accounts followed
- `statuses_count`: Number of tweets/posts
- `location`: User's location (if provided)
- `created_at`: When the account was created

### Performance Features

- Automatic cursor tracking for pagination
- Rate limit detection and handling
- Detailed progress statistics
- Resumable sessions
- Duplicate prevention
</details>

## About This Project

This project was created to provide a free alternative to Twitter's paid API for basic data collection needs. It works by simulating browser requests rather than using official API endpoints, which makes it:

1. **Free to use** - No API keys or paid subscriptions required
2. **Potentially fragile** - May break if Twitter changes their internal APIs
3. **For educational purposes** - A learning tool for understanding social networks

## Disclaimer

This toolkit is for educational and research purposes only. It's designed to help researchers and community managers explore Twitter data without the expense of the official API.

**Important:**
- Use responsibly and respect Twitter's Terms of Service and rate limits
- The developers are not responsible for any misuse or violations of Twitter's terms
- This approach may break at any time if Twitter changes their internal systems
