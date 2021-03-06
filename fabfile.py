#!/usr/bin/python
# vim: set fileencoding=utf-8 :

from fabric.api import *
from fabric.contrib.console import confirm
from os import path
import cmd
import ConfigParser

config = ConfigParser.RawConfigParser()
config.read('deploy.cfg')

currentBranch = ''
processBranches = ['develop', 'testing', 'master', 'recipe', 'staging', 'production']
localBranches = []
source = ''
destination = ''
environnements = config.sections()
localModifs = False

def hasModifs( remote = False):
    """docstring for hasModifs"""
    if not remote:
        #gsp = local("git status --porcelain")
        gsp = local("git status", True)
    else:
        #gsp = run("git status --porcelain")
        gsp = run("git status", True)
    gspArr = gsp.splitlines()
    for line in gspArr:
        #print line
        #if line[0] == 'M':
        if line == '# Changed but not updated:':
            #if not remote:
                #print "Des modifications de fichiers existent."
                #print "Veuillez comitter celles-ci ou lancer la commande 'git stash' pour les stocker, et 'git stash pop' pour les récupérer apres avoir relancé ce script."
                #print gsp
                #abort("Sortie")
            #else:
                return True

def checkModifs():
    """docstring for checkModifs"""
    if hasModifs() and confirm("Des modifications existent: Voulez-vous les stocker par un 'git stash' ?"):
        stash = local("git stash")
        if not stash.failed:
            global localModifs
            localModifs = True
        else:
            print("'git stash' a échoué.")
            print "Veuillez comitter les modifications ou lancer la commande 'git stash' pour les stocker, et 'git stash pop' pour les récupérer apres avoir relancé ce script."
            abort("Sortie du script")

def restoreModifs():
    """docstring for restoreModifs"""
    if localModifs:
        pop = local("git stash pop")
        if pop.failed:
            print("La restauration des modifications par 'git stash pop' a échoué ...")

class Source(cmd.Cmd):
    prompt = "Branche source (? for help) --> "
    #def do_current(self, value):
        #"""current branch"""
        #setSource(currentBranch)
        #return True

    def do_develop(self, value):
        """develop"""
        setSource(self.lastcmd)
        return True

    def do_testing(self, value):
        """testing"""
        setSource(self.lastcmd)
        return True

    def do_master(self, value):
        """master"""
        setSource(self.lastcmd)
        return True

    def do_recipe(self, value):
        """recipe"""
        setSource(self.lastcmd)
        return True

    def do_staging(self, value):
        """staging"""
        setSource(self.lastcmd)
        return True

    def do_quit(self, value):
        """quit"""
        setSource('quit')
        return True

    def do_EOF(self, line):
        return True

def setSource(branch):
    """Set source Branch"""
    global source
    source = branch
    #print "Branche source : " + branch

class Destination(cmd.Cmd):
    prompt = "Branche destination (? for help) --> "

    def testDestination(self, branch):
        """docstring for testDestination"""
        return processBranches.index(source) < processBranches.index(branch)

    def setDestination(self, branch):
        """Set destination Branch"""
        if not self.testDestination(branch):
            return False
        global destination
        destination = branch
        #print "Branche destination : " + branch
        return True

    def do_develop(self, value):
        """develop"""
        return self.setDestination(self.lastcmd)

    def do_testing(self, value):
        """testing"""
        return self.setDestination(self.lastcmd)

    def do_master(self, value):
        """master"""
        return self.setDestination(self.lastcmd)

    def do_recipe(self, value):
        """recipe"""
        return self.setDestination(self.lastcmd)

    def do_staging(self, value):
        """staging"""
        return self.setDestination(self.lastcmd)

    def do_production(self, value):
        """production"""
        return self.setDestination(self.lastcmd)

    def do_quit(self, value):
        """quit"""
        global destination
        destination = self.lastcmd
        return True

    def do_EOF(self, line):
        return True


def test():
    """docstring for test"""
    Destination().cmdloop()

def getCurrentBranch():
    """Retrieve current branch name"""
    branches = local("git branch", True)
    global currentBranch
    currentBranch = branches.split('* ')[1].split('\n')[0]
    print("current branch : " + currentBranch)
    return currentBranch

def checkBranch(branch):
    """check if branch exists"""
    return branch in localBranches

def retrieveBranches():
    """init : Retrieve local branches"""
    names = local("git branch", True).split('\n')
    global localBranches
    for branchName in names:
        localBranches.append(branchName.strip(' *'))

#def checkBranches():
    #"""Check if process branches exists"""
    #global localBranches
    #localBranches = local("git branch", True).split('\n')
    ##print("local branches : ")
    #for branch in localBranches:
        #print(branch)
    #print("process branches : ")
    #for processBranch in processBranches:
        #print(processBranch)

def createLocalBranch(branch):
    """docstring for createLocalBranch"""
    #print("git branch " + branch + " origin/" + branch)
    local("git branch " + branch + " origin/" + branch)

def pushTobranch():
    """docstring for pushTobranch"""
    indexSource = processBranches.index(source) + 1
    #print('source ' + str(indexSource))
    indexDestination = processBranches.index(destination) + 1
    #print('destination ' + str(indexDestination))
    for branch in processBranches[indexSource:indexDestination]:
        #print(branch)
        if not checkBranch(branch):
            createLocalBranch(branch)
        updateBranch(branch)


def updateBranch(branch):
    """Update branch with previous process branch"""
    prevBranch = processBranches[processBranches.index( branch ) - 1]
    #verif index > 0

    #print("git checkout " + branch)
    #print("git pull origin " + branch)
    #if not prevBranch == "production":
        #print("git merge " + prevBranch)
    #print("git push origin " + branch)

    local("git checkout " + branch)
    #local("git pull origin " + branch)
    local("git pull")
    #local("git rebase " + prevBranch)
    if not prevBranch == "production":
        local("git merge " + prevBranch)
    local("git push origin " + branch)
    updateEnv(branch)

def cleanError(host, error, envHasModifs = False, command = False):
    """docstring for eanError"""
    print("sur " + host)
    print("l'erreur suivante est survenue :")
    print(error)
    if confirm("Ouvrir un shell sur l'environnement ?"):
        print("'exit' ou ctrl-d pour revenir au script")
        if envHasModifs:
            print "Attention, un 'git stash' a été effectué, et un 'git stash pop' vous sera prorosé avant l'arret du script ou sera effectué automatiquement si vous décidez de reprendre l'éxécution normale"
        open_shell(command)
    if not confirm("Poursuivre l'exécution du script ?"):
        if envHasModifs and confirm("Des modifications ont étées sauvegardée par un 'git stash'. Voulez-vous les restaurer par un 'git stash pop' ?"):
            pop = run("git stash pop")
            if not pop.failed:
                print "Modifications restaurées"

        abort("Script interronpu par l'utilisateur")
    pass

def updateEnv(branch):
    """docstring for updateEnv"""
    #print branch
    if config.has_section(branch):
        env.user = config.get(branch, 'user')
        env.host_string = config.get(branch, 'host')
        env.warn_only = config.get(branch, 'warn_only')
        url = config.get(branch, 'url')
        source = config.get(branch, 'source')
        vardir = config.get(branch, 'vardir')
        sudopull = config.has_option(branch, 'sudopull')
        envHasModifs = False

        #print env.user
        #print env.host_string
        #print url
        #print source
        #print vardir
        with cd(url):
            with cd(source):
                pwd = path.normpath(run('pwd', True))
                confPwd = path.normpath(url + '/' + source)
                if not pwd == confPwd:
                    #print pwd
                    #print confPwd
                    cleanError(env.host_string, "Mauvais url ou source dans le fichier de conf", envHasModifs, "cd " + confPwd)

                #cleanError(env.host_string, "test porcelain", envHasModifs, "cd " + confPwd)

                if hasModifs( True ):
                    envHasModifs = True
                    run("git stash")


                if sudopull:
                    print sudopull
                    pull = run("sudo git pull origin " + branch)
                else:
                    #print("git pull origin " + branch)
                    pull = run("git pull origin " + branch)


                if pull.failed:
                    cleanError(env.host_string, pull, envHasModifs, "cd " + confPwd)
                if envHasModifs:
                    run("git stash pop")

            pwd = run('pwd', True)
            #print("rm -fr var/cache/* " + "var/" + vardir + "/cache/*")
            rm  = run("rm -fr var/cache/* " + "var/" + vardir + "/cache/*")
            if rm.failed:
                cleanError(env.host_string, rm, envHasModifs, "cd " + url)

def restoreCurrentBranch():
    """docstring for restoreCurrentBranch"""
    local("git checkout " + currentBranch)

def deploy():
    """main deploy tool"""
    #hasModifs()
    checkModifs()
    print("deploy start")
    getCurrentBranch()
    #commit()
    retrieveBranches()
    Source().cmdloop()
    if source == 'quit':
        return
    Destination().cmdloop()
    if destination == 'quit':
        return
    updateBranch(source)
    updateEnv(source)
    pushTobranch()
    restoreCurrentBranch()
    restoreModifs()
