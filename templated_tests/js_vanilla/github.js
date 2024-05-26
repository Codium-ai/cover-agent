class Github {
  constructor() {
    this.client_id = 'ab7e3c6ac10d3714249a';
    this.client_secret = 'f315c3cc4bca8b4b922fc04af1b31b02cb1d143d';
    this.repos_count = 5;
    this.repos_sort = 'created: asc';
  }

  async getUser(user) {
    const profileResponse = await fetch(
      `https://api.github.com/users/${user}?client_id=${this.client_id}&client_secret=${this.client_secret}`
    );
    const reposResponse = await fetch(
      `https://api.github.com/users/${user}/repos?per_page=${this.repos_count}&sort=${this.repos_sort}&client_id=${this.client_id}&client_secret=${this.client_secret}`
    );

    const profile = await profileResponse.json();
    const repos = await reposResponse.json();

    return {
      profile: profile,
      repos: repos,
    };
  }
}
