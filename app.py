from flask import Flask, render_template, request, Response
import subprocess, os, tempfile

app = Flask(__name__)
app.secret_key = 'replace_with_secure_key'

BASE_DIR     = os.path.dirname(__file__)
UPLOAD_DIR   = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

TRAIN_SCRIPT = os.path.join(BASE_DIR, 'train.py')
TEST_SCRIPT  = os.path.join(BASE_DIR, 'test.py')

# flag definitions: (type, is_flag)
TRAIN_FLAGS = {
    'epochs':        ('int',   False),
    'batch_size':    ('int',   False),
    'img_size':      ('list',  False),
    'rect':          ('bool',  True),
    'resume':        ('bool',  True),
    'nosave':        ('bool',  True),
    'notest':        ('bool',  True),
    'noautoanchor':  ('bool',  True),
    'evolve':        ('bool',  True),
    'bucket':        ('str',   False),
    'cache_images':  ('bool',  True),
    'image_weights': ('bool',  True),
    'device':        ('str',   False),
    'multi_scale':   ('bool',  True),
    'single_cls':    ('bool',  True),
    'adam':          ('bool',  True),
    'sync_bn':       ('bool',  True),
    'workers':       ('int',   False),
    'project':       ('str',   False),
    'entity':        ('str',   False),
    'name':          ('str',   False),
    'exist_ok':      ('bool',  True),
    'quad':          ('bool',  True),
    'linear_lr':     ('bool',  True),
    'label_smoothing':('float',False),
    'upload_dataset':('bool',  True),
    'bbox_interval': ('int',   False),
    'save_period':   ('int',   False),
    'artifact_alias':('str',   False),
    'freeze':        ('list',  False),
    'v5_metric':     ('bool',  True),
}

TEST_FLAGS = {
    'batch_size':  ('int',   False),
    'img_size':    ('int',   False),
    'conf_thres':  ('float', False),
    'iou_thres':   ('float', False),
    'task':        ('str',   False),
    'save_txt':    ('bool',  True),
    'save_json':   ('bool',  True),
    'save_hybrid': ('bool',  True),
    'save_conf':   ('bool',  True),
    'augment':     ('bool',  True),
    'verbose':     ('bool',  True),
    'project':     ('str',   False),
    'name':        ('str',   False),
    'exist_ok':    ('bool',  True),
    'no_trace':    ('bool',  True),
    'v5_metric':   ('bool',  True),
}

def get_path_arg(name):
    """Return an uploaded file path if present, else the text field."""
    file_field = f"{name}_file"
    text_field = f"{name}_path"

    if file_field in request.files:
        f = request.files[file_field]
        if f.filename:
            # save to temp and return path
            _, ext = os.path.splitext(f.filename)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext, dir=UPLOAD_DIR)
            f.save(tmp.name)
            return tmp.name

    return request.args.get(text_field)

def build_cmd(mode):
    """Assemble the command based on mode ('train' or 'test')."""
    if mode == 'train':
        script = TRAIN_SCRIPT
        flags  = TRAIN_FLAGS
        paths  = ('weights','cfg','data','hyp')
    else:
        script = TEST_SCRIPT
        flags  = TEST_FLAGS
        paths  = ('weights','data')

    cmd = ['python', script]

    # first handle file/text path args
    for pname in paths:
        p = get_path_arg(pname)
        if p:
            cmd += [f'--{pname}', p]

    # now other flags
    for opt, (typ, is_flag) in flags.items():
        val = request.args.get(opt)
        if not val:
            continue
        if is_flag:
            if val == 'on':
                cmd.append(f"--{opt}")
        else:
            if typ == 'list':
                items = [x for x in val.replace(',', ' ').split() if x]
                cmd += [f"--{opt}"] + items
            else:
                cmd += [f"--{opt}", val]

    return cmd

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_stream')
def run_stream():
    mode = request.args.get('mode','train')
    cmd  = build_cmd(mode)

    def generate():
        proc = subprocess.Popen(cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                text=True,
                                bufsize=1)
        for line in proc.stdout:
            yield f"data: {line.rstrip()}\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)
