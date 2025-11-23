async function loadJSON(path){
  const res = await fetch(path);
  if(!res.ok) throw new Error('Failed to load '+path);
  return res.json();
}

function el(tag, cls, html){
  const e = document.createElement(tag);
  if(cls) e.className = cls;
  if(html !== undefined) e.innerHTML = html;
  return e;
}

async function renderList(){
  const meta = await loadJSON('posts/posts.json');
  const container = document.getElementById('posts');
  container.innerHTML = '';
  meta.forEach(p => {
    const card = el('div','post-card');
    const a = el('a','post-title',p.title);
    a.href = '#'+p.slug;
    a.addEventListener('click', (ev)=>{ev.preventDefault(); openPost(p.slug)});
    const metaEl = el('div','post-meta', `${p.date} — ${p.excerpt}`);
    card.appendChild(a);
    card.appendChild(metaEl);
    container.appendChild(card);
  });
}

async function openPost(slug){
  history.pushState({slug}, '', '#'+slug);
  const listView = document.getElementById('list-view');
  const postView = document.getElementById('post-view');
  const postContent = document.getElementById('post-content');
  listView.classList.add('hidden');
  postView.classList.remove('hidden');
  postContent.innerHTML = '<p>Loading…</p>';
  try{
    const res = await fetch('posts/'+slug+'.html');
    if(!res.ok) throw new Error('post not found');
    const html = await res.text();
    postContent.innerHTML = html;
    window.scrollTo(0,0);
  }catch(e){
    postContent.innerHTML = '<p>Could not load post.</p>';
  }
}

function closePost(){
  history.pushState({}, '', location.pathname);
  document.getElementById('post-view').classList.add('hidden');
  document.getElementById('list-view').classList.remove('hidden');
}

window.addEventListener('popstate', (e)=>{
  const s = location.hash.replace('#','');
  if(s) openPost(s); else closePost();
});

document.getElementById && (async ()=>{
  document.getElementById('back').addEventListener('click', closePost);
  await renderList();
  const hash = location.hash.replace('#','');
  if(hash) openPost(hash);
})();
