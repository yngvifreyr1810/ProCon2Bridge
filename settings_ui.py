"""GPL-3.0-or-later. Local settings, no keyboard injection or timed macros."""
import json
from protocol import OUTPUT_BUTTONS,mapping_targets
from configuration import load_config,update_config

def parse_action(text):
    parts=[p.strip().upper() for p in text.split('+')]
    targets=mapping_targets(parts)
    return 'NONE' if not targets else targets[0] if len(targets)==1 else list(targets)

def format_action(value): return ' + '.join(mapping_targets(value)) or 'NONE'

def open_settings(directory,smoke_test=False):
    import tkinter as tk
    from tkinter import ttk,messagebox
    path=directory/'config.json';cfg=load_config(path)
    root=tk.Tk();root.title('ProCon2Bridge - Back buttons');root.minsize(620,355)
    root.option_add('*Font','{Segoe UI} 10')
    panel=ttk.Frame(root,padding=24);panel.pack(fill='both',expand=True)
    panel.columnconfigure(1,weight=1)
    ttk.Label(panel,text='Back buttons',font=('Segoe UI',17,'bold')).grid(row=0,column=0,columnspan=2,sticky='w',pady=(0,8))
    ttk.Label(panel,text='Assign GL / GR to a Switch Pro button or a simultaneous chord.').grid(row=1,column=0,columnspan=2,sticky='w')
    ttk.Label(panel,text='Examples: B, L_STICK, ZL + ZR. NONE disables a back button.').grid(row=2,column=0,columnspan=2,sticky='w',pady=(4,18))
    values={};boxes=[]
    for row,(source,label) in enumerate((('GL','GL - left back button'),('GR','GR - right back button')),3):
        ttk.Label(panel,text=label).grid(row=row,column=0,sticky='w',padx=(0,20),pady=8)
        values[source]=tk.StringVar(value=format_action(cfg['button_mapping'].get(source,'NONE')))
        box=ttk.Combobox(panel,textvariable=values[source],values=('NONE',*OUTPUT_BUTTONS),width=30)
        box.grid(row=row,column=1,sticky='ew',pady=8);boxes.append(box)
    result=tk.StringVar(value='Save applies while the bridge runs; no reconnect is needed.')
    feedback=ttk.Label(panel,textvariable=result,wraplength=570)
    feedback.grid(row=5,column=0,columnspan=2,sticky='w',pady=(10,10))
    status=tk.StringVar(value='Checking controller...')
    ttk.Label(panel,textvariable=status,wraplength=570).grid(row=6,column=0,columnspan=2,sticky='w')
    actions=ttk.Frame(panel);actions.grid(row=7,column=0,columnspan=2,sticky='e',pady=(20,0))
    def save():
        try:
            patch={key:parse_action(value.get()) for key,value in values.items()}
            update_config(path,mappings=patch)
        except (ValueError,OSError) as error:
            result.set(str(error));feedback.configure(foreground='#b42318');boxes[0].focus_set();return False
        for key,value in values.items():value.set(format_action(patch[key]))
        feedback.configure(foreground='#146c43')
        result.set('Saved. The running bridge applies changes within one second.');return True
    def disable():
        for value in values.values():value.set('NONE')
        save()
    ttk.Button(actions,text='Disable both',command=disable).pack(side='left',padx=(0,10))
    ttk.Button(actions,text='Save mappings',command=save).pack(side='left',padx=(0,10))
    ttk.Button(actions,text='Close',command=root.destroy).pack(side='left')
    def refresh():
        try:
            state=json.loads((directory/'status.json').read_text(encoding='utf-8'))
            held=[b for b in state.get('buttons',[]) if b in ('GL','GR')]
            outputs=state.get('mapped_buttons',[])
            status.set('Controller: '+state['state']+' | Back: '+(', '.join(held) or 'released')+'\nOutput: '+(', '.join(outputs) or 'none')+' (hold a button for 1 second to inspect)')
        except (OSError,ValueError,KeyError):status.set('Bridge is not running. Mappings will apply on next launch.')
        root.after(400,refresh)
    root.bind('<Control-s>',lambda _:save());root.bind('<Escape>',lambda _:root.destroy())
    boxes[0].focus_set();refresh()
    if smoke_test:
        root.update()
        assert root.winfo_width()>=620
        for widget in boxes:
            assert widget.winfo_width()>150 and widget.winfo_ismapped()
        values['GL'].set('ZL + ZR');values['GR'].set('B');assert save()
        saved=load_config(path);assert saved['button_mapping']['GL']==['ZL','ZR']
        assert saved['button_mapping']['GR']=='B'
        root.destroy();return
    root.mainloop()
