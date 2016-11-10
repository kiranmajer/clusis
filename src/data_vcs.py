import git

rep = git.Repo('/home/kiran/cluster/clusis_3f/')
idx=rep.index

def vcs_commit(sha_id, commit_msgs):
    msg_str = 
    rep.git.commit('-a', "-m 'Changed mdata again.'")