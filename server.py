import os, json, socket, urllib.request, urllib.error
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT=Path(__file__).parent
OLLAMA_URL=os.getenv('OLLAMA_URL','http://127.0.0.1:11434/api/generate')
OLLAMA_MODEL=os.getenv('OLLAMA_MODEL','llava')
OPENROUTER_KEY=os.getenv('OPENROUTER_API_KEY','')
OPENROUTER_MODEL=os.getenv('OPENROUTER_MODEL','openrouter/free')
PROVIDER=os.getenv('LLM_PROVIDER','openrouter').lower()  # openrouter | ollama | auto

SYSTEM='''You are an educational wellness assistant. Review a user-provided image and optional user-entered vital measurements. Do not identify the person. Do not diagnose diseases, estimate medical conditions, or infer sensitive traits, emotions, personality, age, ethnicity, or other health conditions from appearance. Do not claim that vitals were measured from the image. Only describe clearly visible, non-sensitive features relevant to image usability and general wellness context, such as lighting, blur, obstruction, and whether the image appears to show a person. Combine this cautiously with the user-entered vitals. Return STRICT JSON with keys: image_observations (array of strings), wellness_summary (string), recommendations (array of strings), limitations (string). Keep recommendations general and educational. If vital values are concerning, recommend seeking advice from a qualified healthcare professional rather than diagnosing.'''

def demo():
    return {'mode':'demo','image_observations':['Image was received, but no LLM analysis was available.'], 'wellness_summary':'The project can still demonstrate the workflow, but this result is not an AI image analysis.', 'recommendations':['Configure a free LLM provider to enable multimodal image analysis.'], 'limitations':'Demo fallback only; not medical advice or diagnosis.'}

def ollama(image_data, vitals):
    if not image_data or ',' not in image_data: raise ValueError('A captured or uploaded image is required.')
    b64=image_data.split(',',1)[1]
    prompt=SYSTEM+'\n\nUser-entered vitals: '+json.dumps(vitals)+'\nReturn JSON only.'
    payload={'model':OLLAMA_MODEL,'prompt':prompt,'images':[b64],'stream':False,'format':'json'}
    req=urllib.request.Request(OLLAMA_URL,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=180) as r: raw=json.loads(r.read())
    out=json.loads(raw.get('response','{}')); out['mode']='ollama'; out['model']=OLLAMA_MODEL; return out

def openrouter(image_data, vitals):
    if not OPENROUTER_KEY: raise RuntimeError('OPENROUTER_API_KEY is not configured.')
    if not image_data or ',' not in image_data: raise ValueError('A captured or uploaded image is required.')
    prompt=SYSTEM+'\n\nUser-entered vitals: '+json.dumps(vitals)+'\nAnalyze the image and vitals within the stated limits. Return JSON only.'
    payload={
      'model':OPENROUTER_MODEL,
      'messages':[{'role':'user','content':[{'type':'text','text':prompt},{'type':'image_url','image_url':{'url':image_data}}]}],
      'temperature':0.2,
      'max_tokens':900
    }
    req=urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+OPENROUTER_KEY,'HTTP-Referer':'http://localhost','X-Title':'Wellness School Project'})
    with urllib.request.urlopen(req,timeout=180) as r: raw=json.loads(r.read())
    text=raw['choices'][0]['message']['content']
    if isinstance(text,list): text=''.join(x.get('text','') if isinstance(x,dict) else str(x) for x in text)
    text=str(text).strip()
    if text.startswith('```'):
        text=text.split('\n',1)[1] if '\n' in text else text
        text=text.rsplit('```',1)[0].strip()
    out=json.loads(text); out['mode']='openrouter'; out['model']=OPENROUTER_MODEL; return out

def analyze(image, vitals):
    errors=[]
    if PROVIDER in ('openrouter','auto'):
        try: return openrouter(image,vitals)
        except Exception as e: errors.append('OpenRouter: '+str(e))
        if PROVIDER=='openrouter': raise RuntimeError('; '.join(errors))
    if PROVIDER in ('ollama','auto'):
        try: return ollama(image,vitals)
        except Exception as e: errors.append('Ollama: '+str(e))
    raise RuntimeError('; '.join(errors) or 'No LLM provider configured.')

class Handler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path!='/api/wellness-analysis': self.send_error(404); return
        try:
            n=int(self.headers.get('Content-Length','0')); data=json.loads(self.rfile.read(n))
            try: result=analyze(data.get('image'),data.get('vitals',{}))
            except Exception as e:
                if os.getenv('DEMO_FALLBACK','false').lower()=='true': result=demo(); result['llm_error']=str(e)
                else: raise
            body=json.dumps(result).encode(); self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
        except Exception as e:
            body=json.dumps({'error':str(e)}).encode(); self.send_response(500); self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(body)

if __name__=='__main__':
    os.chdir(ROOT); port=int(os.getenv('PORT','8000'))
    print('Wellness Tool running at http://localhost:%s' % port)
    print('LLM provider:', PROVIDER)
    if PROVIDER in ('openrouter','auto'):
        print('OpenRouter model:', OPENROUTER_MODEL, '| key configured:', bool(OPENROUTER_KEY))
    ThreadingHTTPServer(('0.0.0.0',port),Handler).serve_forever()
