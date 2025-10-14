#!/usr/bin/env python3
"""
GitHub Repository Fetcher GUI Application
A simple GUI application to fetch and display GitHub repositories for a user.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import json
from datetime import datetime
import webbrowser
import threading


class GitHubRepoFetcher:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub Repository Fetcher")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Data and state for sorting/filtering
        self.all_repos = []
        self.filtered_repos = []
        self.repos_by_id = {}
        self.sort_state = {}  # e.g., {"Stars": True}
        self.current_sort_col = "Stars"
        self.current_sort_desc = True  # default sort by Stars desc
        self.column_titles = {
            "Name": "Repository Name",
            "Description": "Description",
            "Language": "Language",
            "Stars": "⭐ Stars",
            "Forks": "🍴 Forks",
            "Updated": "Last Updated",
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        # Repo frame will be placed at row 4 after adding filters at row 3
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="GitHub Repository Fetcher", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Username input section
        ttk.Label(main_frame, text="GitHub Username:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.username_var = tk.StringVar(value="Lanthanum89")  # Default to your username
        self.username_entry = ttk.Entry(main_frame, textvariable=self.username_var, width=30)
        self.username_entry.grid(row=1, column=1, sticky="we", padx=(10, 0), pady=5)
        
        # Fetch button
        self.fetch_button = ttk.Button(main_frame, text="Fetch Repositories", 
                                      command=self.fetch_repositories_threaded)
        self.fetch_button.grid(row=1, column=2, padx=(10, 0), pady=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=2, column=0, columnspan=3, sticky="we", pady=10)
        
        # Filters area
        self.setup_filters(main_frame)
        
        # Repository display area
        self.setup_repo_display(main_frame)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready to fetch repositories")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=5, column=0, columnspan=3, sticky="we", pady=(10, 0))
        
        # Bind Enter key to fetch
        self.username_entry.bind('<Return>', lambda e: self.fetch_repositories_threaded())
    
    def setup_filters(self, parent):
        """Create filter controls (search, language, min stars, include forks)."""
        filters = ttk.LabelFrame(parent, text="Filters", padding="6")
        filters.grid(row=3, column=0, columnspan=3, sticky="we", pady=(0, 10))
        for i in range(8):
            filters.columnconfigure(i, weight=0)
        filters.columnconfigure(3, weight=1)  # Search entry can expand

        # Search
        ttk.Label(filters, text="Search:").grid(row=0, column=0, sticky=tk.W, padx=(0, 6))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(filters, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=1, columnspan=3, sticky="we", padx=(0, 12))
        self.search_entry.bind('<KeyRelease>', lambda e: self.apply_filters())

        # Language
        ttk.Label(filters, text="Language:").grid(row=0, column=4, sticky=tk.W, padx=(0, 6))
        self.language_var = tk.StringVar(value="All")
        self.language_combo = ttk.Combobox(filters, textvariable=self.language_var, values=["All"], state='readonly', width=18)
        self.language_combo.grid(row=0, column=5, sticky=tk.W, padx=(0, 12))
        self.language_combo.bind('<<ComboboxSelected>>', lambda e: self.apply_filters())

        # Min Stars
        ttk.Label(filters, text="Min Stars:").grid(row=0, column=6, sticky=tk.W, padx=(0, 6))
        self.min_stars_var = tk.IntVar(value=0)
        try:
            self.min_stars_spin = ttk.Spinbox(filters, from_=0, to=100000, textvariable=self.min_stars_var, width=8)
        except Exception:
            self.min_stars_spin = tk.Spinbox(filters, from_=0, to=100000, textvariable=self.min_stars_var, width=8)
        self.min_stars_spin.grid(row=0, column=7, sticky=tk.W)
        # Apply on input changes
        for ev in ('<KeyRelease>', '<FocusOut>'):
            self.min_stars_spin.bind(ev, lambda e: self.apply_filters())

        # Second row
        self.include_forks_var = tk.BooleanVar(value=True)
        include_forks_cb = ttk.Checkbutton(filters, text="Include forks", variable=self.include_forks_var, command=self.apply_filters)
        include_forks_cb.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(6, 0))

        reset_btn = ttk.Button(filters, text="Clear Filters", command=self.reset_filters)
        reset_btn.grid(row=1, column=7, sticky=tk.E, pady=(6, 0))
        
    def setup_repo_display(self, parent):
        """Set up the repository display area with Treeview"""
        # Frame for repository list
        repo_frame = ttk.LabelFrame(parent, text="Repositories", padding="5")
        repo_frame.grid(row=4, column=0, columnspan=3, sticky="nsew", pady=10)
        repo_frame.columnconfigure(0, weight=1)
        repo_frame.rowconfigure(0, weight=1)
        
        # Create Treeview with scrollbars
        columns = ("Name", "Description", "Language", "Stars", "Forks", "Updated")
        self.tree = ttk.Treeview(repo_frame, columns=columns, show="headings", height=15)
        
        # Configure column headings and widths
        # Bind heading clicks for sorting
        for col in columns:
            self.tree.heading(col, text=self.column_titles[col], command=lambda c=col: self.sort_by(c))
        
        self.tree.column("Name", width=200, minwidth=150)
        self.tree.column("Description", width=300, minwidth=200)
        self.tree.column("Language", width=100, minwidth=80)
        self.tree.column("Stars", width=80, minwidth=60)
        self.tree.column("Forks", width=80, minwidth=60)
        self.tree.column("Updated", width=120, minwidth=100)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(repo_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(repo_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="we")
        
        # Bind double-click to open repository
        self.tree.bind("<Double-1>", self.open_repository)
        
        # Context menu
        self.setup_context_menu()
        
    def setup_context_menu(self):
        """Set up right-click context menu for repository items"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Open in Browser", command=self.open_repository)
        self.context_menu.add_command(label="Copy Clone URL", command=self.copy_clone_url)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Repository Details", command=self.show_repo_details)
        
        self.tree.bind("<Button-3>", self.show_context_menu)
        
    def show_context_menu(self, event):
        """Show context menu on right-click"""
        item = self.tree.selection()[0] if self.tree.selection() else None
        if item:
            self.context_menu.post(event.x_root, event.y_root)
            
    def fetch_repositories_threaded(self):
        """Fetch repositories in a separate thread to avoid blocking the UI"""
        threading.Thread(target=self.fetch_repositories, daemon=True).start()
        
    def fetch_repositories(self):
        """Fetch repositories from GitHub API"""
        username = self.username_var.get().strip()
        
        if not username:
            messagebox.showerror("Error", "Please enter a GitHub username")
            return
            
        # Update UI to show loading state
        self.root.after(0, self.set_loading_state, True)
        self.root.after(0, self.status_var.set, f"Fetching repositories for {username}...")
        
        try:
            # Construct API URL
            api_url = f"https://api.github.com/users/{username}/repos"
            
            # Make API request
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            
            repos_data = response.json()
            
            # Update UI with results
            self.root.after(0, self.display_repositories, repos_data)
            self.root.after(0, self.status_var.set, 
                          f"Successfully fetched {len(repos_data)} repositories for {username}")
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Error fetching repositories: {str(e)}"
            self.root.after(0, messagebox.showerror, "API Error", error_msg)
            self.root.after(0, self.status_var.set, "Error occurred while fetching repositories")
            
        except json.JSONDecodeError:
            self.root.after(0, messagebox.showerror, "Error", "Invalid response from GitHub API")
            self.root.after(0, self.status_var.set, "Invalid API response")
            
        finally:
            self.root.after(0, self.set_loading_state, False)
            
    def set_loading_state(self, loading):
        """Set the loading state of the UI"""
        if loading:
            self.progress.start()
            self.fetch_button.config(state=tk.DISABLED)
        else:
            self.progress.stop()
            self.fetch_button.config(state=tk.NORMAL)
            
    def display_repositories(self, repos_data):
        """Store data, populate filters, sort, and render tree items."""
        # Store full dataset
        self.all_repos = repos_data or []
        
        # Populate language options
        self.set_language_options()
        
        # Apply filters + sort + render
        self.apply_filters()

    def set_language_options(self):
        """Populate the language dropdown from the current data set."""
        langs = set()
        for repo in self.all_repos:
            lang = repo.get('language') or 'Unknown'
            langs.add(lang)
        options = ['All'] + sorted(langs)
        self.language_combo['values'] = options
        # Keep selection if still valid
        if self.language_var.get() not in options:
            self.language_var.set('All')

    def apply_filters(self):
        """Apply current filter controls and refresh the table."""
        q = (self.search_var.get() or '').strip().lower()
        lang = self.language_var.get()
        try:
            min_stars = int(self.min_stars_var.get())
        except Exception:
            min_stars = 0
            self.min_stars_var.set(0)
        include_forks = bool(self.include_forks_var.get())

        def matches(repo):
            # language filter
            repo_lang = repo.get('language') or 'Unknown'
            if lang and lang != 'All' and repo_lang != lang:
                return False
            # min stars
            if (repo.get('stargazers_count') or 0) < min_stars:
                return False
            # forks
            if not include_forks and repo.get('fork'):
                return False
            # search in name and description
            if q:
                name = (repo.get('name') or '').lower()
                desc = (repo.get('description') or '').lower()
                if q not in name and q not in desc:
                    return False
            return True

        self.filtered_repos = [r for r in self.all_repos if matches(r)]
        self.sort_current()
        self.render_tree_items(self.filtered_repos)

    def reset_filters(self):
        """Reset all filters to defaults and re-apply."""
        self.search_var.set('')
        self.language_var.set('All')
        self.min_stars_var.set(0)
        self.include_forks_var.set(True)
        self.apply_filters()

    def render_tree_items(self, repos):
        """Render the given list of repos into the tree view."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Rebuild id mapping
        self.repos_by_id = {}

        for repo in repos:
            repo_id = str(repo.get('id'))
            self.repos_by_id[repo_id] = repo

            name = repo.get('name', 'N/A')
            description = repo.get('description', 'No description') or 'No description'
            language = repo.get('language', 'Unknown') or 'Unknown'
            stars = repo.get('stargazers_count', 0)
            forks = repo.get('forks_count', 0)
            
            updated_at = repo.get('updated_at', '')
            if updated_at:
                try:
                    updated_date = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                    updated_str = updated_date.strftime('%Y-%m-%d')
                except Exception:
                    updated_str = updated_at[:10]
            else:
                updated_str = 'Unknown'

            if len(description) > 50:
                description = description[:47] + "..."

            self.tree.insert("", tk.END, iid=repo_id, values=(name, description, language, stars, forks, updated_str))

    def sort_by(self, column):
        """Toggle sort for the given column and refresh."""
        if self.current_sort_col == column:
            # Toggle direction
            self.current_sort_desc = not self.current_sort_desc
        else:
            self.current_sort_col = column
            # Default direction: Stars/Forks/Updated desc, others asc
            self.current_sort_desc = column in ("Stars", "Forks", "Updated")
        self.sort_current()
        self.render_tree_items(self.filtered_repos)
        self.update_sort_indicators()

    def sort_current(self):
        """Sort the filtered_repos using current sort state."""
        col = self.current_sort_col
        desc = self.current_sort_desc
        def keyfunc(repo):
            # Map columns to comparable values
            if col == 'Name':
                return (repo.get('name') or '').lower()
            if col == 'Description':
                return (repo.get('description') or '').lower()
            if col == 'Language':
                return (repo.get('language') or 'zzzz').lower()
            if col == 'Stars':
                return int(repo.get('stargazers_count') or 0)
            if col == 'Forks':
                return int(repo.get('forks_count') or 0)
            if col == 'Updated':
                ts = repo.get('updated_at') or ''
                try:
                    return datetime.fromisoformat(ts.replace('Z', '+00:00'))
                except Exception:
                    return datetime.min
            return 0
        self.filtered_repos.sort(key=keyfunc, reverse=desc)

    def update_sort_indicators(self):
        """Update column headers to show sort direction."""
        for col, base in self.column_titles.items():
            indicator = ''
            if col == self.current_sort_col:
                indicator = ' ▼' if self.current_sort_desc else ' ▲'
            self.tree.heading(col, text=base + indicator, command=lambda c=col: self.sort_by(c))
            
    def open_repository(self, event=None):
        """Open selected repository in web browser"""
        selection = self.tree.selection()
        if not selection:
            return
        
        repo_id = selection[0]
        repo = self.repos_by_id.get(repo_id)
        if repo:
            webbrowser.open(repo['html_url'])
            
    def copy_clone_url(self):
        """Copy clone URL to clipboard"""
        selection = self.tree.selection()
        if not selection:
            return
        
        repo_id = selection[0]
        repo = self.repos_by_id.get(repo_id)
        if repo:
            clone_url = repo['clone_url']
            self.root.clipboard_clear()
            self.root.clipboard_append(clone_url)
            self.status_var.set(f"Copied clone URL for {repo.get('name','repo')}")
            
    def show_repo_details(self):
        """Show detailed information about selected repository"""
        selection = self.tree.selection()
        if not selection:
            return
        
        repo_id = selection[0]
        repo = self.repos_by_id.get(repo_id)
        if repo:
            self.show_repo_details_window(repo)
            
    def show_repo_details_window(self, repo):
        """Show repository details in a new window"""
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Repository Details - {repo['name']}")
        details_window.geometry("600x500")
        details_window.transient(self.root)
        
        # Create scrolled text widget
        text_widget = scrolledtext.ScrolledText(details_window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Format repository details
        details = f"""Repository: {repo['name']}
Owner: {repo['owner']['login']}
Description: {repo.get('description', 'No description')}

🌐 URL: {repo['html_url']}
📁 Clone URL: {repo['clone_url']}
🏠 Homepage: {repo.get('homepage', 'Not specified')}

📊 Statistics:
  ⭐ Stars: {repo.get('stargazers_count', 0)}
  🍴 Forks: {repo.get('forks_count', 0)}
  👁️ Watchers: {repo.get('watchers_count', 0)}
  📝 Open Issues: {repo.get('open_issues_count', 0)}
  📏 Size: {repo.get('size', 0)} KB

🔧 Details:
  💻 Language: {repo.get('language', 'Not specified')}
  🏷️ Default Branch: {repo.get('default_branch', 'main')}
  📅 Created: {repo.get('created_at', '')[:10]}
  🔄 Updated: {repo.get('updated_at', '')[:10]}
  
🔒 Visibility: {'Public' if not repo.get('private', False) else 'Private'}
🍴 Fork: {'Yes' if repo.get('fork', False) else 'No'}
📚 Has Wiki: {'Yes' if repo.get('has_wiki', False) else 'No'}
📄 Has Pages: {'Yes' if repo.get('has_pages', False) else 'No'}

🏷️ Topics: {', '.join(repo.get('topics', [])) if repo.get('topics') else 'None'}

📜 License: {repo.get('license', {}).get('name', 'Not specified') if repo.get('license') else 'Not specified'}
"""
        
        text_widget.insert(tk.END, details)
        text_widget.config(state=tk.DISABLED)  # Make read-only


def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = GitHubRepoFetcher(root)
    
    # Center the window on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()


if __name__ == "__main__":
    main()