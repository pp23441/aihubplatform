from github import Github

def list_public_repos(user):
    g = Github()
    user = g.get_user(user)
    return [repo.name for repo in user.get_repos()[:5]]
