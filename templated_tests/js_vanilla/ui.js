export default class UI {
  constructor() {
    this.profile = document.getElementById('profile');
  }
  showProfile(user) {
    this.profile.innerHTML = `
            <div class="card card-body mb-3">
                <div class="row">
                    <div class="col-md-3">
                        <img src="${user.avatar_url}" alt="" class="img-fluid mb-2">
                        <a href="${user.html_url}" target="_blank" class="btn btn-primary btn-block"> View Profile</a>
                    </div>
                    <div class="col-md-9">
                        <span class="badge badge-primary"> Public Repos: ${user.public_repos}</span>
                        <span class="badge badge-secondary"> Public Gists: ${user.public_gists}</span>
                        <span class="badge badge-success"> Followers: ${user.followers}</span>
                        <span class="badge badge-info"> Following: ${user.following}</span>
                        <br> <br>
                        <ul class="list-group">
                            <li class="list-group-item">Company : ${user.company}</li>
                            <li class="list-group-item">Website : ${user.blog}</li>
                            <li class="list-group-item">Location : ${user.location}</li>
                            <li class="list-group-item">Member Since : ${user.created_at}</li>
                        </ul>
                    </div>
                </div>
            </div>
            <h3 class="page-heading mb-3"> Latest Repos</h3>
            <div id="repos"></div>
            </div>
        `;
  }

  showRepos(repos) {
    let output = '';

    repos.forEach(function (repo) {
      output += `
            <div class="card card-body mb-2">
                <div class="row">
                    <div class="col-sm-6">
                        <a href="${repo.html_url}" target="_blank">${repo.name}</a>
                        <p class="pt-2">${repo.description}</p>
                    </div>
                    <div class="col-sm-6">
                        <span class="badge badge-primary"> Starts: ${repo.stargazers_count}</span>
                        <span class="badge badge-info"> Watchers: ${repo.watchers_count}</span>
                        <span class="badge badge-light"> Forks: ${repo.forms_count}</span>
                    </div>
                </div>
            </div>            
            `;
    });

    document.getElementById('repos').innerHTML = output;
  }

  showAlert(message, className) {
    this.clearAlert();
    const div = document.createElement('div');
    div.className = className;
    div.appendChild(document.createTextNode(message));
    const container = document.querySelector('.searchContainer');
    const search = document.querySelector('.search');
    container.insertBefore(div, search);

    setTimeout(() => {
      this.clearAlert();
    }, 2000);
  }

  clearAlert() {
    const currentAlert = document.querySelector('.alert');
    if (currentAlert) {
      currentAlert.remove();
    }
  }

  clearProfile() {
    this.profile.innerHTML = '';
  }
}
