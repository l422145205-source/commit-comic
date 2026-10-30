# Evidence notes / 来源说明

Git range: `f66d4b84097ef6369eea619f63dbca2b4a95aeba..0e8443a8e3486215a91198e4b2beb4ec6525f792`

Panel references prove a source link, not semantic faithfulness, deployment or user impact.

## Panel 1 / summary

Sources: R1

### R1

reports/production_pilot.json

[Pinned public source](https://github.com/l422145205-source/voxstage/blob/0e8443a8e3486215a91198e4b2beb4ec6525f792/reports/production_pilot.json)

Source file SHA-256: `1765b6ea254d643798349b184930e071cbbc49a22027e47641e94e2e27d0d5f8`

Selected JSON fields from the pinned historical report; original file hash retained. Not a newly executed result or external-user feedback.

    {
      "selection": "showcases[spaceport].one_line_edit",
      "changed_cue_ids": [
        "s01"
      ],
      "stats": {
        "tts_calls": 1,
        "asr_calls": 1,
        "tts_cache_hits": 3,
        "asr_cache_hits": 7
      },
      "status": "complete",
      "accepted_cues": [
        "s01",
        "s02",
        "s03",
        "s04"
      ],
      "scope": "ASR-based content and deterministic timing/acoustic checks only. No human MOS, emotion accuracy, speaker similarity, fine-tuning or production traffic claims."
    }

## Panel 2 / summary

Sources: E1

### E1

src/voxstage/director.py

[Pinned public source](https://github.com/l422145205-source/voxstage/commit/0e8443a8e3486215a91198e4b2beb4ec6525f792)

Reviewed excerpt of a public GitHub parent-to-commit diff. Selected files only; no new execution implied.

    +    def take(self,scene,cue,speaker,attempt,previous_issues):
    +        instruction=INSTRUCTIONS[cue.tone]
    +        if attempt>1:
    +            if previous_issues==['duration_overflow']:
    +                instruction+=' 语速快一些，保持吐字清楚。Speak faster while remaining clear.'
    +            else:
    +                instruction+=' 逐字清晰朗读，不漏字、不重复。Articulate every word clearly without omissions or repetitions.'
    +        seed=(scene.seed+attempt*1009+int(key(cue.id)[:6],16))%(2**31-1)
    +        parameters={'text':cue.spoken,'language':cue.language,'speaker':speaker,'instruct':instruction,'seed':seed}
    +        take_key=key({'version':1,'backend':self.backend.identity,**parameters})
    +        folder=self.cache/'tts'/take_key; raw=folder/'raw.wav';meta=folder/'take.json'
    +        folder.mkdir(parents=True,exist_ok=True)
    +        with exclusive(folder/'take.lock'):
    +            cached=None
    +            if meta.exists() and raw.exists():
    +                candidate=json.loads(meta.read_text(encoding='utf-8'))
    +                if candidate.get('sha256')==audio.digest(raw):cached=candidate
    +            if cached is None:
    +                self.event('synthesize',cue_id=cue.id,attempt=attempt)
    +                self.stats['tts_calls']+=1
    +                result=self.backend.synthesize(**parameters,output=raw)
    +                signal=audio.analyze(raw)
    +                cached={'take_key':take_key,'sha256':signal['sha256'],'parameters':parameters,'synthesis':result}
    +                atomic_json(meta,cached)
    +            else:
    +                self.stats['tts_cache_hits']+=1;self.event('reuse_take',cue_id=cue.id,attempt=attempt)
    +        self.event('verify_content',cue_id=cue.id,attempt=attempt)
    +        signal=audio.analyze(raw)
    +        transcript=self.transcribe(raw,cue.language)
    +        content=compare(cue.spoken,transcript['text'])
    +        issues=diagnose(cue,scene.policy,signal,content)
    +        result={'take_key':take_key,'cue_id':cue.id,'attempt':attempt,'raw_signal':signal,
    +            'asr':transcript,'content':content,'issues':issues,'parameters':parameters}
    +        if not issues:
    +            fit_key=key({'version':1,'take_sha256':signal['sha256'],'capacity':cue.capacity,
    +                         'max_speedup':scene.policy.max_speedup})
    +            fitted=folder/(fit_key+'.wav')
    +            try:
    +                with exclusive(folder/(fit_key+'.lock')):
    +                    transform=audio.speed_fit(raw,fitted,cue.capacity,scene.policy.max_speedup)
    +                    final_signal=audio.analyze(fitted)
    +                    final_asr=self.transcribe(fitted,cue.language)
    +                    final_content=compare(cue.spoken,final_asr['text'])
    +                    issues=diagnose(cue,scene.policy,final_signal,final_content)
    +                    if final_signal['duration']>cue.capacity+1/audio.RATE:issues.append('final_duration_overflow')
    +            except ValueError as exc:
    +                result.update(issues=['transform_not_feasible'],transform_error=str(exc))
    +                return result
    +            result.update(transform=transform,final_signal=final_signal,final_asr=final_asr,
    +                          final_content=final_content,issues=issues,path=str(fitted),sha256=final_signal['sha256'])
    +        return result
    +
    +    def run(self,scene,*,interrupt_after_cue=None):
    +        scene=Scene.model_validate(scene.model_dump(mode='json') if isinstance(scene,Scene) else scene)
    +        fingerprint=key({'version':1,'scene':scene.model_dump(mode='json'),'backend':self.backend.identity})
    +        folder=self.root/'data/runs'/(scene.id+'-'+fingerprint[:16])
    +        folder.mkdir(parents=True,exist_ok=True)
    +        with exclusive(folder/'scene.lock'):
    +            return self._run(scene,folder,fingerprint,interrupt_after_cue)
    +
    +    def _run(self,scene,folder,fingerprint,interrupt_after_cue):
    +        started=time.perf_counter();self.stats={k:0 for k in self.stats}
    +        atomic_json(folder/'scene.json',scene.model_dump(mode='json'))
    +        cast={c.id:c.speaker for c in scene.cast};accepted={};records=[];rejected=[]
    +        for cue in scene.cues:
    +            issues=[]
    +            for attempt in range(1,scene.policy.max_attempts+1):
    +                result=self.take(scene,cue,cast[cue.character],attempt,issues)
    +                issues=result['issues'];decision=decide(cue,issues,attempt,scene.policy.max_attempts)
    +                result['decision']=decision.model_dump();records.append(result)
    +                atomic_json(folder/'takes.json',records)
    +                self.event('decision',cue_id=cue.id,attempt=attempt,**decision.model_dump(exclude={'cue_id'}))
    +                if decision.action=='accept':accepted[cue.id]=result;break
    +                if decision.action=='reject':rejected.append(cue.id);break
    +            if interrupt_after_cue==cue.id:
    +                raise RuntimeError('controlled interruption after cue '+cue.id)
    +        result={'scene_id':scene.id,'run_id':folder.name,'request_fingerprint':fingerprint,
    +            'backend':self.backend.label,'backend_identity':self.backend.identity,
    +            'status':'needs_review' if rejected else 'complete','rejected_cues':rejected,
    +            'accepted_cues':list(accepted),'stats':self.stats.copy(),
    +            'elapsed_seconds':time.perf_counter()-started,
    +            'subjective_quality':'style, acting and naturalness require human listening',
    +            'takes':records}
    +        if not rejected:
    +            result['export']=audio.export_scene(scene,accepted,folder/'export')
    +        atomic_json(folder/'result.json',result)
    +        self.event('finished',run_id=folder.name,status=result['status'])
    +        return result

## Panel 3 / summary

Sources: E1

### E1

src/voxstage/director.py

[Pinned public source](https://github.com/l422145205-source/voxstage/commit/0e8443a8e3486215a91198e4b2beb4ec6525f792)

Reviewed excerpt of a public GitHub parent-to-commit diff. Selected files only; no new execution implied.

    +    def take(self,scene,cue,speaker,attempt,previous_issues):
    +        instruction=INSTRUCTIONS[cue.tone]
    +        if attempt>1:
    +            if previous_issues==['duration_overflow']:
    +                instruction+=' 语速快一些，保持吐字清楚。Speak faster while remaining clear.'
    +            else:
    +                instruction+=' 逐字清晰朗读，不漏字、不重复。Articulate every word clearly without omissions or repetitions.'
    +        seed=(scene.seed+attempt*1009+int(key(cue.id)[:6],16))%(2**31-1)
    +        parameters={'text':cue.spoken,'language':cue.language,'speaker':speaker,'instruct':instruction,'seed':seed}
    +        take_key=key({'version':1,'backend':self.backend.identity,**parameters})
    +        folder=self.cache/'tts'/take_key; raw=folder/'raw.wav';meta=folder/'take.json'
    +        folder.mkdir(parents=True,exist_ok=True)
    +        with exclusive(folder/'take.lock'):
    +            cached=None
    +            if meta.exists() and raw.exists():
    +                candidate=json.loads(meta.read_text(encoding='utf-8'))
    +                if candidate.get('sha256')==audio.digest(raw):cached=candidate
    +            if cached is None:
    +                self.event('synthesize',cue_id=cue.id,attempt=attempt)
    +                self.stats['tts_calls']+=1
    +                result=self.backend.synthesize(**parameters,output=raw)
    +                signal=audio.analyze(raw)
    +                cached={'take_key':take_key,'sha256':signal['sha256'],'parameters':parameters,'synthesis':result}
    +                atomic_json(meta,cached)
    +            else:
    +                self.stats['tts_cache_hits']+=1;self.event('reuse_take',cue_id=cue.id,attempt=attempt)
    +        self.event('verify_content',cue_id=cue.id,attempt=attempt)
    +        signal=audio.analyze(raw)
    +        transcript=self.transcribe(raw,cue.language)
    +        content=compare(cue.spoken,transcript['text'])
    +        issues=diagnose(cue,scene.policy,signal,content)
    +        result={'take_key':take_key,'cue_id':cue.id,'attempt':attempt,'raw_signal':signal,
    +            'asr':transcript,'content':content,'issues':issues,'parameters':parameters}
    +        if not issues:
    +            fit_key=key({'version':1,'take_sha256':signal['sha256'],'capacity':cue.capacity,
    +                         'max_speedup':scene.policy.max_speedup})
    +            fitted=folder/(fit_key+'.wav')
    +            try:
    +                with exclusive(folder/(fit_key+'.lock')):
    +                    transform=audio.speed_fit(raw,fitted,cue.capacity,scene.policy.max_speedup)
    +                    final_signal=audio.analyze(fitted)
    +                    final_asr=self.transcribe(fitted,cue.language)
    +                    final_content=compare(cue.spoken,final_asr['text'])
    +                    issues=diagnose(cue,scene.policy,final_signal,final_content)
    +                    if final_signal['duration']>cue.capacity+1/audio.RATE:issues.append('final_duration_overflow')
    +            except ValueError as exc:
    +                result.update(issues=['transform_not_feasible'],transform_error=str(exc))
    +                return result
    +            result.update(transform=transform,final_signal=final_signal,final_asr=final_asr,
    +                          final_content=final_content,issues=issues,path=str(fitted),sha256=final_signal['sha256'])
    +        return result
    +
    +    def run(self,scene,*,interrupt_after_cue=None):
    +        scene=Scene.model_validate(scene.model_dump(mode='json') if isinstance(scene,Scene) else scene)
    +        fingerprint=key({'version':1,'scene':scene.model_dump(mode='json'),'backend':self.backend.identity})
    +        folder=self.root/'data/runs'/(scene.id+'-'+fingerprint[:16])
    +        folder.mkdir(parents=True,exist_ok=True)
    +        with exclusive(folder/'scene.lock'):
    +            return self._run(scene,folder,fingerprint,interrupt_after_cue)
    +
    +    def _run(self,scene,folder,fingerprint,interrupt_after_cue):
    +        started=time.perf_counter();self.stats={k:0 for k in self.stats}
    +        atomic_json(folder/'scene.json',scene.model_dump(mode='json'))
    +        cast={c.id:c.speaker for c in scene.cast};accepted={};records=[];rejected=[]
    +        for cue in scene.cues:
    +            issues=[]
    +            for attempt in range(1,scene.policy.max_attempts+1):
    +                result=self.take(scene,cue,cast[cue.character],attempt,issues)
    +                issues=result['issues'];decision=decide(cue,issues,attempt,scene.policy.max_attempts)
    +                result['decision']=decision.model_dump();records.append(result)
    +                atomic_json(folder/'takes.json',records)
    +                self.event('decision',cue_id=cue.id,attempt=attempt,**decision.model_dump(exclude={'cue_id'}))
    +                if decision.action=='accept':accepted[cue.id]=result;break
    +                if decision.action=='reject':rejected.append(cue.id);break
    +            if interrupt_after_cue==cue.id:
    +                raise RuntimeError('controlled interruption after cue '+cue.id)
    +        result={'scene_id':scene.id,'run_id':folder.name,'request_fingerprint':fingerprint,
    +            'backend':self.backend.label,'backend_identity':self.backend.identity,
    +            'status':'needs_review' if rejected else 'complete','rejected_cues':rejected,
    +            'accepted_cues':list(accepted),'stats':self.stats.copy(),
    +            'elapsed_seconds':time.perf_counter()-started,
    +            'subjective_quality':'style, acting and naturalness require human listening',
    +            'takes':records}
    +        if not rejected:
    +            result['export']=audio.export_scene(scene,accepted,folder/'export')
    +        atomic_json(folder/'result.json',result)
    +        self.event('finished',run_id=folder.name,status=result['status'])
    +        return result

## Panel 4 / summary

Sources: R1

### R1

reports/production_pilot.json

[Pinned public source](https://github.com/l422145205-source/voxstage/blob/0e8443a8e3486215a91198e4b2beb4ec6525f792/reports/production_pilot.json)

Source file SHA-256: `1765b6ea254d643798349b184930e071cbbc49a22027e47641e94e2e27d0d5f8`

Selected JSON fields from the pinned historical report; original file hash retained. Not a newly executed result or external-user feedback.

    {
      "selection": "showcases[spaceport].one_line_edit",
      "changed_cue_ids": [
        "s01"
      ],
      "stats": {
        "tts_calls": 1,
        "asr_calls": 1,
        "tts_cache_hits": 3,
        "asr_cache_hits": 7
      },
      "status": "complete",
      "accepted_cues": [
        "s01",
        "s02",
        "s03",
        "s04"
      ],
      "scope": "ASR-based content and deterministic timing/acoustic checks only. No human MOS, emotion accuracy, speaker similarity, fine-tuning or production traffic claims."
    }

