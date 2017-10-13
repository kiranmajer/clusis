import git
import os.path


class Vcs:
    '''
    Wrapper class like dbshell. Provides a Vcs instance for the vcs methods. Can be
    invoked like this:
    with Vcs(repo_path) as vcs:
        vcs.method_call()
    
    Important:
    Works only on existing git repos, i.e. the repo must be initialized seperately.
    This way no git repos are created unintentionally.
    '''
    def __init__(self, repo_path):
        self._repo_path = repo_path 
        #if not os.path.isdir(os.path.join(self.__repo_path, '.git')):
        #    self.__repo = git.Repo.init(self.__repo_path)
        self._repo = git.Repo(repo_path)
        self._idx = self._repo.index
        
        
    def __enter__(self):
        return self
    
    
    def __exit__(self, exc_type, exc_value, traceback):
        print('Exit Vcs instance at', self._repo_path)
#         del self._idx
#         del self._repo
#         del self._repo_path
    
    
    def __valid_file_list(self, files):
        file_list = []
        if type(files) is list:
            file_list.extend(files)
        elif type(files) is str:
            file_list.append(files)
        else:
            raise ValueError('files must be a single file or a list of files.')
        # try to find valid absolute paths
        valid_file_list = []
        for f in file_list:
            if os.path.isabs(f) and os.path.exists(f) and f.startswith(self._repo_path):
                valid_file_list.append(f)
            elif os.path.exists(os.path.join(self._repo_path, f)):
                valid_file_list.append(os.path.join(self._repo_path, f))
            else:
                raise ValueError('Path incorrect or outside repository or file does not exist: {}.'.format(f))
        return file_list
    
    
    def add_to_index(self, files):
        file_list = self.__valid_file_list(files)
        
        self._idx.add(file_list)
    
    
    def update_gitignore(self, files):
        git_ignore_path = os.path.join(self._repo_path, '.gitignore')
        gitignore_exists = os.path.exists(git_ignore_path)
        if gitignore_exists:
            open_mode = 'a' # append
        else:
            open_mode = 'w' # start at beginning
        file_list = self.__valid_file_list(files)
        with open(git_ignore_path, open_mode)as f:
                f.write('\n'.join(file_list))
                f.write('\n')
        
        if gitignore_exists:
            self.commit_changes('Appended lines to .gitignore.')
            pass
        else:
            self._idx.add([git_ignore_path])
            self.commit_changes('Added new .gitignore to index.')
            
    
    
    def commit_changes(self, short_log, git_options='-a', log=None):
        '''
        Commits all changes (modified, added, deleted ...) to the repository.
        
        short_log: string containing the first log entry or header; obligatory
        git_options: string containing further options for git commit beside log msgs
        log: list or str containing the extended log entries:
             i) a str will just be piped through to git
             ii) in case of a list each list item will be a new paragraph, 
                 e.g '-m log[0], -m log[1]...'. If the list item itself is a list, 
                 each of its elements will be seperated by a new line 
        '''
        if not type(git_options) is str:
            raise ValueError('git_options must be a string.')
        short_log = '-m {}'.format(short_log)
        commit_options_list = [git_options, short_log]
        if type(log) is str:
            commit_options_list.append(log)
        elif type(log) is list:
            for p in log:
                if type(p) is list:
                    commit_options_list.append('-m {}'.format('\n '.join(p)))
                else:
                    commit_options_list.append('m {}'.format(p))
        elif log:
            raise ValueError('"log" must be a list or str.')
  
        try:
            print('Commiting changes:')
            #print(commit_options_list)
            s = self._repo.git.commit(commit_options_list)
            print(s)
        except git.exc.GitCommandError as e:
            print('Commit may have failed, git error: {}'.format(e))
    
    
    def print_status(self):
        print(self._repo.git.status())
    
    