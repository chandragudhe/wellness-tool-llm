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

def _parse_json_from_model_text(text):
    """Parse JSON robustly and return a useful error when a model replies with empty/non-JSON text."""
    if text is None:
        raise ValueError('The LLM returned no message content.')
    if isinstance(text, list):
        text=''.join(x.get('text','') if isinstance(x,dict) else str(x) for x in text)
    text=str(text).strip()
    if not text:
        raise ValueError('The LLM returned an empty response. Try again or use another available vision model.')
    if text.startswith('```'):
        lines=text.splitlines()
        if lines and lines[0].startswith('```'): lines=lines[1:]
        if lines and lines[-1].strip().startswith('```'): lines=lines[:-1]
        text='\n'.join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Extract the first JSON object when the model adds explanatory text.
        first=text.find('{'); last=text.rfind('}')
        if first >= 0 and last > first:
            try: return json.loads(text[first:last+1])
            except json.JSONDecodeError: pass
        raise ValueError('The LLM returned non-JSON content: '+text[:500])

def openrouter(image_data, vitals):
    if not OPENROUTER_KEY: raise RuntimeError('OPENROUTER_API_KEY is not configured.')
    if not image_data or ',' not in image_data: raise ValueError('A captured or uploaded image is required.')
    prompt=SYSTEM+'\n\nUser-entered vitals: '+json.dumps(vitals)+'\nReturn one valid JSON object only. Do not use markdown or code fences.'
    payload={
      'model':OPENROUTER_MODEL,
      'messages':[{'role':'user','content':[{'type':'text','text':prompt},{'type':'image_url','image_url':{'url':image_data}}]}],
      'temperature':0.2,
      'max_tokens':900
    }
    req=urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+OPENROUTER_KEY,'HTTP-Referer':'https://wellness-school-project.example','X-Title':'Wellness School Project'})
    try:
        with urllib.request.urlopen(req,timeout=180) as r:
            raw_bytes=r.read(); status=r.status
    except urllib.error.HTTPError as e:
        detail=e.read().decode('utf-8','replace')
        raise RuntimeError('OpenRouter HTTP %s: %s' % (e.code, detail[:1200]))
    except urllib.error.URLError as e:
        raise RuntimeError('OpenRouter connection error: '+str(e.reason))
    raw_text=raw_bytes.decode('utf-8','replace').strip()
    if not raw_text:
        raise RuntimeError('OpenRouter returned an empty HTTP response.')
    try:
        raw=json.loads(raw_text)
    except json.JSONDecodeError:
        raise RuntimeError('OpenRouter returned non-JSON HTTP content: '+raw_text[:500])
    choices=raw.get('choices') or []
    if not choices:
        raise RuntimeError('OpenRouter response contains no choices: '+json.dumps(raw)[:1000])
    message=choices[0].get('message') or {}
    out=_parse_json_from_model_text(message.get('content'))
    out['mode']='openrouter'; out['model']=raw.get('model',OPENROUTER_MODEL)
    return out

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
