## First time use repo
#### Create dev folder from your home directory
Linux OS
```
mkdir dev 
```
Windows
```
md dev
```

#### clone repo
```
git clone git@github.com:jasonpea/awdawd.git
```

#### go to your 
```
cd awdawd
```

## Using existing repo
#### if you alrady have repo exist, no need clone again, just pull the main branch
```
git checkout main
git pull
```
#### create your development branch e.g.: new_readme
```
git checkout -b new_readme
```
#### create new file or make change existing files using your IDE or Editor
for example update README.md

#### add file
```
git add README.md
```
#### commit your change
```
git commit README.md
```

#### push your change
```
git push origin new_readme
```

#### if your branch behind main run command to sync the latest main to your dev branch
```
git fetch
git merge origin/main
```
booty butt
