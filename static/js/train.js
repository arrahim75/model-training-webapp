// static/js/train.js
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('train-form');
    const out  = document.getElementById('output-container');
  
    form.addEventListener('submit', e => {
      e.preventDefault();
  
      // hide form, show output
      // form.style.display = 'none';
      out.style.display  = 'block';
      out.textContent    = '';  // clear any old logs
  
      // build query string
      const qs = new URLSearchParams(new FormData(form)).toString();
      const es = new EventSource(`/train_stream?${qs}`);
  
      es.onmessage = evt => {
        out.textContent += evt.data + "\n";
        out.scrollTop = out.scrollHeight;
      };
      es.onerror = () => es.close();
    });
  });
  