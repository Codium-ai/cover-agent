// search input
const github = new Github();
const ui = new UI();
const searchUser = document.getElementById('userName');

searchUser.addEventListener('keyup', (e) => {
  const userText = e.target.value;
  if (userText !== '') {
    github.getUser(userText).then((data) => {
      if (data.profile.message === 'Not Found') {
        //show alert
        ui.showAlert('Profile Not Found', 'alert alert-danger');
      } else {
        ui.showProfile(data.profile);
        ui.showRepos(data.repos);
      }
    });
  } else {
    // clear profile
    ui.clearProfile();
  }
});
