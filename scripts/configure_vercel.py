"""After explicit transfer approval, copy allowlisted backend settings via stdin."""
import json
import os
import secrets
import subprocess
from pathlib import Path
from dotenv import dotenv_values

root=Path(__file__).resolve().parents[1]
values=dotenv_values(root/'.env')
settings={k:v for k,v in values.items() if v and k in {'ANTHROPIC_API_KEY','NVIDIA_API_KEY','NVIDIA_API_KEYS','VISION_PROVIDER','ANTHROPIC_VISION_MODEL','ANTHROPIC_REPORT_MODEL','REPORT_MODEL'}}
secret_file=root/'.deploy-secrets.json'
if secret_file.exists(): users=json.loads(secret_file.read_text())
else:
    users={'demo':secrets.token_urlsafe(32)}
    descriptor=os.open(secret_file,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(descriptor,'w') as handle:json.dump(users,handle)
settings.update(STUDIO_USERS_JSON=json.dumps(users),STUDIO_ENV='production',MAX_DAILY_JOBS_PER_USER='3',MAX_DAILY_JOBS='10',MAX_PENDING_JOBS='4')
for key,value in settings.items():
    result=subprocess.run(['vercel','env','add',key,'production','--force','--sensitive','--yes','--scope','glomeyo'],cwd=root,input=value.encode(),capture_output=True)
    print(key+': '+('configured' if result.returncode==0 else 'FAILED'),flush=True)
    if result.returncode:raise SystemExit(1)
print('Backend secrets configured. Login credentials stored only in .deploy-secrets.json.')
