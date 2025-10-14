# GitHub Repository Fetcher

A simple GUI application to fetch and display GitHub repositories for any user.

## Features

- 🔍 Fetch repositories for any GitHub user
- 📊 Display repository information in a sortable table (click column headers)
- 🔽 Click-to-sort by any column; click again to toggle ascending/descending
- ⭐ Default sort by stars (most starred first)
- 🌐 Open repositories in your web browser
- 📋 Copy clone URLs to clipboard
- 📄 View detailed repository information
- 🎨 Clean and intuitive user interface

## Requirements

- Python 3.6 or higher
- tkinter (usually comes with Python)
- requests library

## Installation

1. Clone or download this repository
2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:

   ```bash
   python github_repo_fetcher.py
   ```

2. Enter a GitHub username (default is "Lanthanum89")
3. Click "Fetch Repositories" or press Enter
4. Browse through the repositories in the table

## Features in Detail

### Repository Display

- **Name**: Repository name
- **Description**: Short description of the repository
- **Language**: Primary programming language
- **Stars**: Number of stars (⭐)
- **Forks**: Number of forks (🍴)
- **Updated**: Last update date

### Interactive Features

- **Double-click** any repository to open it in your web browser
- **Right-click** for context menu with options:
  - Open in Browser
  - Copy Clone URL
  - Repository Details

### Filtering

- Search: type to filter by name/description
- Language: pick from detected languages or "All"
- Min Stars: filter by minimum stargazer count
- Include forks: toggle to hide/show forked repos

### Repository Details Window

Shows comprehensive information including:

- Owner information
- URLs (repository, clone, homepage)
- Statistics (stars, forks, watchers, issues)
- Technical details (language, default branch, dates)
- Visibility and features (public/private, wiki, pages)
- Topics and license information

## Screenshot

The application provides a clean, tabular view of repositories with sorting capabilities and detailed information available on demand.

## API Usage

This application uses the GitHub REST API endpoint:

```text
https://api.github.com/users/{username}/repos
```

No authentication is required for public repositories, but GitHub has rate limits for unauthenticated requests (60 requests per hour per IP address).

## Error Handling

The application includes comprehensive error handling for:

- Network connectivity issues
- Invalid usernames
- API rate limits
- Malformed responses

## License

This project is open source and available under the MIT License.
