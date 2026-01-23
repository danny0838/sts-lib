{% if not single_page -%}

import {Unicode, StsDict} from "./sts.js";

{% endif -%}

function* walkThroughAnchors(anchor, direction) {
  let a = anchor;
  if (direction > 0) {
    while (a = a.nextElementSibling) {
      yield a;
    }
    if (a = anchor.parentNode.firstElementChild) {
      yield a;
      while (a = a.nextElementSibling) {
        yield a;
      }
    }
    return;
  }
  if (direction < 0) {
    while (a = a.previousElementSibling) {
      yield a;
    }
    if (a = anchor.parentNode.lastElementChild) {
      yield a;
      while (a = a.previousElementSibling) {
        yield a;
      }
    }
    return;
  }
}

function moveAnchor(anchor, offset, filter) {
  let i = Math.abs(offset);
  for (const a of walkThroughAnchors(anchor, offset)) {
    if (a === anchor) {
      break;
    }
    if (!a.matches('a[tabindex]')) {
      continue;
    }
    if (typeof filter !== "function" || filter(a)) {
      if (i > 1) {
        i--;
        continue;
      }
      return a;
    }
  }
  return null;
}

function moveCandidate(anchor, offset, filter) {
  const cands = anchor.querySelectorAll('ins');
  const len = cands.length;

  // no cand, it's impossible to move
  if (len === 0) {
    return -1;
  }

  let cand = anchor.querySelector('ins:not([hidden])');
  let idx = Array.prototype.indexOf.call(cands, cand);
  let candNew;
  idx += offset;
  if (idx >= len) { idx = len - 1; }
  if (idx < 0) { idx = 0; }
  candNew = cands[idx];
  if (typeof filter !== "function" || filter(candNew)) {
    return idx;
  }
  return -1;
}

function setCandidate(anchor, idx) {
  if (idx < 0) {
    return setCandidateDel(anchor);
  }
  return setCandidateIns(anchor, idx);
}

function setCandidateIns(anchor, idx) {
  const cands = anchor.querySelectorAll('ins');
  const cand = cands[idx];
  if (!cand) { return false; }

  anchor.querySelector('del').hidden = true;
  for (const c of cands) {
    c.hidden = true;
  }
  cand.hidden = false;

  for (const elem of anchor.querySelectorAll('span')) {
    elem.remove();
  }
  markPicked(anchor);
  return true;
}

function setCandidateDel(anchor) {
  const cand = anchor.querySelector('del');
  if (!cand) { return false; }

  cand.hidden = false;
  for (const c of anchor.querySelectorAll('ins')) {
    c.hidden = true;
  }

  for (const elem of anchor.querySelectorAll('span')) {
    elem.remove();
  }
  markPicked(anchor);
  return true;
}

function setCandidateCustom(anchor, text) {
  for (const c of anchor.querySelectorAll('del, ins')) {
    c.hidden = true;
  }

  let elem = anchor.querySelector('span');
  if (!elem) {
    elem = anchor.appendChild(document.createElement('span'));
  }
  if (typeof text === 'string') {
    elem.textContent = text;
  }

  markPicked(anchor);
  return true;
}

function markChecked(anchor) {
  if (!anchor.classList.contains('unchecked')) {
    return;
  }
  if ('skipCheck' in anchor.dataset) {
    return;
  }
  anchor.classList.add('checked');
  anchor.classList.remove('unchecked');
}

function unmarkChecked(anchor) {
  if (!anchor.classList.contains('checked')) {
    return;
  }
  anchor.classList.add('unchecked');
  anchor.classList.remove('checked');

  // Add a temporary skipCheck mark to prevent being immediately re-checked
  // when re-focused.
  anchor.dataset.skipCheck = '';
  setTimeout(() => {
    delete anchor.dataset.skipCheck;
  }, 200);
}

function markPicked(anchor) {
  anchor.classList.add('picked');

  // picked implies checked
  markChecked(anchor);
}

function unmarkPicked(anchor) {
  anchor.classList.remove('picked');
}

function toggleEditing(anchor, willEdit) {
  if (typeof willEdit === 'undefined') {
    willEdit = !anchor.classList.contains('editing');
  }

  if (willEdit) {
    // edited implies picked
    markPicked(anchor);

    anchor.classList.add('editing');
    let elem = anchor.querySelector('span');
    if (!elem) {
      const cand = anchor.querySelector('del:not([hidden]), ins:not([hidden])');
      setCandidateCustom(anchor, cand.textContent);
      elem = anchor.querySelector('span');
    }
    elem.contentEditable = true;
    elem.focus();
    const onBlur = elem.addEventListener('blur', (event) => {
      elem.removeEventListener('blur', onBlur);
      toggleEditing(anchor, false);
    });
  } else {
    anchor.classList.remove('editing');
    const elem = anchor.querySelector('span');
    elem.contentEditable = false;
    elem.textContent = elem.textContent;
    anchor.focus();
  }
}

function editContext(anchor) {
  function convertTextNodeToAnchor(textNode) {
    const newElem = document.createElement('a');
    newElem.tabIndex = 0;
    newElem.classList.add('unmatched');
    const del = newElem.appendChild(document.createElement('del'));
    anchor.parentNode.insertBefore(newElem, textNode);
    del.appendChild(textNode);
  }

  const prev = anchor.previousSibling;
  if (prev && prev.nodeType === 3) {
    convertTextNodeToAnchor(prev);
  }

  const next = anchor.nextSibling;
  if (next && next.nodeType === 3) {
    convertTextNodeToAnchor(next);
  }
}

{%- if not single_page %}

async function dismissPhrase(anchor) {
  const origTextNode = anchor.querySelector('del').firstChild;
  const origComps = Unicode.split(origTextNode.nodeValue);
  if (!(origComps.length >= 2)) { return; }

  removePopup();
  const {dict} = convertHtml.lastOptions;
  const prevNode = anchor.previousSibling;
  const parent = anchor.parentNode;

  // split current anchor into shorter text nodes
  parent.replaceChild(origTextNode, anchor);
  origComps.pop();
  origTextNode.splitText(origComps.join('').length);

  // create a placeholder element at the split point
  const ph = document.createElement('span');
  parent.replaceChild(ph, origTextNode);

  // insert the re-converted shortened text
  ph.insertAdjacentHTML('beforebegin', _convertHtml(dict, origTextNode.nodeValue));

  // re-convert following nodes and replace changed parts
  {
    const nextNodes = (() => {
      const rv = [];
      let node = ph;
      while (node = node.nextSibling) {
        if (node.nodeType === 1 && !node.matches('a[tabindex]')) {
          break;
        }
        rv.push(node);
      }
      return rv;
    })();
    const nextText = nextNodes.map(x => getText(x)).join('');
    const tpl = document.createElement('template');
    tpl.innerHTML = _convertHtml(dict, nextText);
    const nextNodesNew = Array.from(tpl.content.childNodes);

    // calculate the position where the unchanged parts start
    // skip nextNodes[0] and nextNodesNew[0], to always convert the latter part
    // of the splitted text node
    let iOld = nextNodes.length - 1;
    let iNew = nextNodesNew.length - 1;
    while (iOld >= 1 && iNew >= 1) {
      const nodeOld = nextNodes[iOld];
      const nodeNew = nextNodesNew[iNew];
      if (getText(nodeOld) !== getText(nodeNew)) {
        break;
      }
      iOld--;
      iNew--;
    }
    for (let i = 0; i <= iOld; i++) {
      parent.removeChild(nextNodes[i]);
    }
    for (let i = 0; i <= iNew; i++) {
      parent.insertBefore(nextNodesNew[i], ph);
    }

    function getText(node) {
      switch (node.nodeType) {
        case 1:
          return node.querySelector('del').textContent;
        case 3:
          return node.nodeValue;
        default:
          // this should not happen;
          return '';
      }
    }
  }
  ph.remove();

  evaluator = prevNode ?
    document.evaluate('following-sibling::a[@tabindex]', prevNode, null, 0) :
    document.evaluate('./a[@tabindex]', parent, null, 0);
  const anchorNext = evaluator.iterateNext();
  if (anchorNext) { anchorNext.focus(); }
}

{%- endif %}

function moveToUnchecked(anchor, offset) {
  const anchorNew = moveAnchor(anchor, offset, a => {
    return a.matches('.unchecked');
  });
  if (!anchorNew) {
    return;
  }
  anchorNew.focus();
}

function moveToCheckworthy(anchor, offset) {
  const anchorNew = moveAnchor(anchor, offset, a => {
    return a.matches('.unchecked, .checked, .picked');
  });
  if (!anchorNew) {
    return;
  }
  anchorNew.focus();
}

function moveToSame(anchor, offset) {
  let current = anchor.querySelector('del').textContent;
  const anchorNew = moveAnchor(anchor, offset, a => {
    return a.querySelector('del').textContent === current;
  });
  if (!anchorNew) {
    return;
  }
  anchorNew.focus();
}

function moveToChanged(anchor, offset) {
  const anchorNew = moveAnchor(anchor, offset, a => {
    return a.matches('.changed');
  });
  if (!anchorNew) {
    return;
  }
  anchorNew.focus();
}

function moveToAny(anchor, offset) {
  const anchorNew = moveAnchor(anchor, offset);
  if (!anchorNew) {
    return;
  }
  anchorNew.focus();
}

function toggleCandidate(anchor, offset) {
  const idxNew = moveCandidate(anchor, offset);
  if (idxNew === -1) { return; }
  setCandidate(anchor, idxNew);
}

function autoPick(anchor, mode) {
  const modes = {
    "applyBackwardUnchecked": "將目前選字套用至前面所有未審的相同字",
    "applyForwardUnchecked": "將目前選字套用至後面所有未審的相同字",
    "applyAllUnchecked": "將目前選字套用至全文所有未審的相同字",
    "applyBackward": "將目前選字套用至前面所有相同字",
    "applyForward": "將目前選字套用至後面所有相同字",
    "applyAll": "將目前選字套用至全文所有相同字",
  };

  if (typeof mode === 'undefined') {
    const idxMap = Array.from(Object.keys(modes));
    const options = idxMap.map((mode, i) => `${i + 1}.${modes[mode]}`);
    const msg = "請指定自動套用方式：\n" + options.join('\n');
    const idx = parseInt(prompt(msg), 10);
    mode = idxMap[idx - 1];
  }

  if (!modes[mode]) {
    return;
  }

  const func = (() => {
    const customCand = anchor.querySelector('span');
    if (customCand) {
      const text = customCand.textContent;
      return a => setCandidateCustom(a, text);
    } else {
      const cands = anchor.querySelectorAll('ins');
      const candCur = anchor.querySelector('ins:not([hidden])');
      const candIdx = Array.prototype.indexOf.call(cands, candCur);
      return a => setCandidate(a, candIdx);
    }
  })();

  const viewer = document.querySelector('#viewer');
  const anchors = viewer.querySelectorAll('a[tabindex]:not(.unmatched)');
  const charCur = anchor.querySelector('del').textContent;

  func(anchor);

  let start, end;
  if (["applyBackwardUnchecked", "applyBackward"].includes(mode)) {
    start = 0;
    end = Array.prototype.indexOf.call(anchors, anchor);
  } else if (["applyForwardUnchecked", "applyForward"].includes(mode)) {
    start = Array.prototype.indexOf.call(anchors, anchor) + 1;
    end = anchors.length;
  } else if (["applyAllUnchecked", "applyAll"].includes(mode)) {
    start = 0;
    end = anchors.length;
  }

  for (let i = start; i < end; i++) {
    const a = anchors[i];
    if (a === anchor) {
      continue;
    }
    if (a.querySelector('del').textContent !== charCur) {
      continue;
    }
    if (["applyBackwardUnchecked", "applyForwardUnchecked", "applyAllUnchecked"].includes(mode) &&
        !a.matches('.unchecked')) {
      continue;
    }
    func(a);
  }

  anchor.focus();
}

async function runCommand(anchor, cmd) {
  const cmds = {
    "moveToUncheckedBackward": "移至上一個未審字",
    "moveToUncheckedForward": "移至下一個未審字",
    "moveToCheckworthyBackward": "移至上一個待校字",
    "moveToCheckworthyForward": "移至下一個待校字",
    "moveToSameBackward": "移至上一個相同字",
    "moveToSameForward": "移至下一個相同字",
    "moveToChangedBackward": "移至上一個異動字",
    "moveToChangedForward": "移至下一個異動字",
    "moveToAnyBackward": "移至上一個字",
    "moveToAnyForward": "移至下一個字",

    "applyBackwardUnchecked": "將目前選字套用至前面所有未審的相同字",
    "applyForwardUnchecked": "將目前選字套用至後面所有未審的相同字",
    "applyAllUnchecked": "將目前選字套用至全文所有未審的相同字",
    "applyBackward": "將目前選字套用至前面所有相同字",
    "applyForward": "將目前選字套用至後面所有相同字",
    "applyAll": "將目前選字套用至全文所有相同字",

    "unmarkChecked": "取消標記已審字",
    "unmarkPicked": "取消標記已選字",

    "toggleEditing": "編輯文字",
    "editContext": "編輯前後文字",

{%- if not single_page %}

    "dismissPhrase": "重新分割為較短詞語",

{%- endif %}
  };

  if (typeof cmd === 'undefined') {
    if (typeof HTMLDialogElement !== 'undefined') {
      const dialog = document.getElementById('viewer-options');
      const section = dialog.querySelector('form section');

      // init options for commands for the first time
      if (!section.children.length) {
        for (const cmd in cmds) {
          const label = section.appendChild(document.createElement('label'));
          const input = label.appendChild(document.createElement('input'));
          input.type = 'radio';
          input.name = 'cmd';
          input.value = cmd;
          label.appendChild(document.createTextNode(cmds[cmd]));
        }
        section.querySelector('input').checked = true;
      }

      // reset autofocus to the currently checked element
      for (const elem of section.querySelectorAll('[autofocus]')) {
        elem.autofocus = false;
      }
      section.querySelector(':checked').autofocus = true;

      cmd = await new Promise((resolve, reject) => {
        function onClose(event) {
          dialog.removeEventListener('close', onClose);
          const rv = dialog.returnValue ? dialog.querySelector('form').cmd.value : null;
          resolve(rv);
        }
        dialog.addEventListener('close', onClose);
        dialog.returnValue = '';
        dialog.showModal();
      });
    } else {
      const idxMap = Array.from(Object.keys(cmds));
      const options = idxMap.map((cmd, i) => `${i + 1}.${cmds[cmd]}`);
      const msg = "請輸入要執行的指令：\n" + options.join('\n');
      const idx = parseInt(prompt(msg), 10);
      cmd = idxMap[idx - 1];
    }
  }

  if (!cmds[cmd]) {
    return;
  }

  switch (cmd) {
    case "moveToUncheckedBackward":
      moveToUnchecked(anchor, -1);
      break;
    case "moveToUncheckedForward":
      moveToUnchecked(anchor, 1);
      break;
    case "moveToCheckworthyBackward":
      moveToCheckworthy(anchor, -1);
      break;
    case "moveToCheckworthyForward":
      moveToCheckworthy(anchor, 1);
      break;
    case "moveToSameBackward":
      moveToSame(anchor, -1);
      break;
    case "moveToSameForward":
      moveToSame(anchor, 1);
      break;
    case "moveToChangedBackward":
      moveToChanged(anchor, -1);
      break;
    case "moveToChangedForward":
      moveToChanged(anchor, 1);
      break;
    case "moveToAnyBackward":
      moveToAny(anchor, -1);
      break;
    case "moveToAnyForward":
      moveToAny(anchor, 1);
      break;
    case "applyBackwardUnchecked":
    case "applyForwardUnchecked":
    case "applyAllUnchecked":
    case "applyBackward":
    case "applyForward":
    case "applyAll":
      autoPick(anchor, cmd);
      break;
    case "unmarkChecked":
      unmarkChecked(anchor);
      break;
    case "unmarkPicked":
      unmarkPicked(anchor);
      break;
    case "toggleEditing":
      toggleEditing(anchor);
      break;
    case "editContext":
      editContext(anchor);
      break;
{%- if not single_page %}
    case "dismissPhrase":
      dismissPhrase(anchor);
      break;
{%- endif %}
  }
}

function showPopup(anchor) {
  const popup = document.createElement('aside');

  const onMouseDown = (event) => {
    if (event.button !== 0) {
      return;
    }

    if (event.shiftKey || event.ctrlKey || event.altKey || event.metaKey) {
      return;
    }

    event.preventDefault();
    const a = event.target;
    setCandidate(anchor, a.tabIndex - 1);
  };

  // del
  {
    const cand = anchor.querySelector('del');
    const b = popup.appendChild(document.createElement('b'));
    const a = b.appendChild(document.createElement('a'));
    a.textContent = cand.textContent;
    a.tabIndex = 0;
    a.addEventListener('mousedown', onMouseDown);
  }

  // command
  {
    const a = popup.appendChild(document.createElement('a'));
    a.textContent = '→';
    a.tabIndex = 0;
    a.addEventListener('mousedown', (event) => {
      event.preventDefault();
      runCommand(anchor);
    });
  }

  // ins
  {
    const cands = anchor.querySelectorAll('ins');
    for (let i = 0, I = cands.length; i < I; i++) {
      const cand = cands[i];
      const a = popup.appendChild(document.createElement('a'));
      a.textContent = cand.textContent;
      a.tabIndex = i + 1;
      a.addEventListener('mousedown', onMouseDown);
    }
  }

  popup.classList.add('popup');
  popup.style.top = getOffsetY(anchor) + 'px';
  const parent = anchor.offsetParent;
  parent.appendChild(popup);
  const x_avail = Math.max(parent.offsetWidth - popup.offsetWidth - 5, 0);
  let x = Math.min(getOffsetX(anchor), x_avail);
  popup.style.left = x + 'px';
}

function removePopup() {
  for (const elem of document.querySelectorAll('.popup')) {
    elem.remove();
  }
}

function getOffsetX(field) {
  let offset = 0;
  while (field) {
    offset += field.offsetLeft;
    field = field.offsetParent;
  }
  return offset;
}

function getOffsetY(field) {
  let offset = 0;
  while (field) {
    offset += field.offsetTop;
    field = field.offsetParent;
  }
  return offset;
}

function onKeyDown(event) {
  const target = event.target.closest('a');
  if (!target) { return; }

  // special combinations
  if (event.shiftKey && event.key === "~" && !target.matches('.editing')) {
    event.preventDefault();
    editContext(target);
    return;
  }

  if (event.shiftKey || event.ctrlKey || event.altKey || event.metaKey) {
    return;
  }

  if (target.matches('.editing')) {
    switch (event.key) {
      case "`":
      case "Escape": {
        event.preventDefault();
        toggleEditing(target);
        break;
      }
    }
    return;
  }

  switch (event.key) {
    case "`": {
      event.preventDefault();
      toggleEditing(target);
      break;
    }
    case "q": case "e": {
      event.preventDefault();
      const offset = event.key === "e" ? 1 : -1;
      moveToUnchecked(target, offset);
      break;
    }
    case "a": case "d": {
      event.preventDefault();
      const offset = event.key === "d" ? 1 : -1;
      moveToCheckworthy(target, offset);
      break;
    }
    case "z": case "c": {
      event.preventDefault();
      const offset = event.key === "c" ? 1 : -1;
      moveToSame(target, offset);
      break;
    }
    case "w": case "s": {
      event.preventDefault();
      const offset = event.key === "s" ? 1 : -1;
      toggleCandidate(target, offset);
      break;
    }
    case "0": case "1": case "2": case "3": case "4":
    case "5":case "6": case "7": case "8": case "9": {
      event.preventDefault();
      const idx = parseInt(event.key, 10) - 1;
      setCandidate(target, idx);
      break;
    }
    case "Enter": {
      event.preventDefault();
      runCommand(target);
      break;
    }
    case "Escape": {
      event.preventDefault();
      removePopup();
      break;
    }
  }
}

function onFocus(event) {
  const target = event.target.closest('a');
  if (!target) { return; }

  // remove popup when editing
  if (target.matches('.editing')) {
    removePopup();
    return;
  }

  markChecked(target);
  removePopup();
  showPopup(target);
}

function onBlur(event) {
  const target = event.target.closest('a');
  if (!target) { return; }
  removePopup();
}

document.addEventListener('DOMContentLoaded', (event) => {
  const viewer = document.querySelector('#viewer');
  viewer.addEventListener('keydown', onKeyDown);
  viewer.addEventListener('focus', onFocus, true);
  viewer.addEventListener('blur', onBlur, true);

  for (const elem of viewer.querySelectorAll('a')) {
    elem.tabIndex = 0;
    const atomic = elem.hasAttribute('atomic');
    if (atomic) {
      elem.removeAttribute('atomic');
      elem.classList.add('atomic');
    }
    const insElems = elem.querySelectorAll('ins');
    const cls = (atomic && insElems.length <= 1) ? 'single' : 'unchecked';
    elem.classList.add(cls);
    if (insElems[0] && elem.querySelector('del').textContent !== insElems[0].textContent) {
      elem.classList.add('changed');
    }
  }

  const target = viewer.querySelector('a.unchecked');
  if (target) { target.focus(); }
});

{%- if not single_page %}

const excludeRegexPattern = /^\/(.*)\/([a-z]*)$/;

function parseExcludePattern(exclude) {
  if (!exclude) { return null; }
  let source = exclude, flags = 'g';
  const m = excludeRegexPattern.exec(exclude);
  if (m) {
    source = m[1];
    flags = new Set(m[2]);
    flags.add('g');
    flags.delete('y');
    flags = [...flags.values()].join('');
  }
  return new RegExp(source, flags);
}

const dictInfo = new WeakMap();

async function loadDict(mode, customDict) {
  // check cache
  const cached = dictInfo.get(loadDict.lastDict);
  if (cached && cached.mode === mode && cached.customDict === customDict) {
    return loadDict.lastDict;
  }

  const url = `dicts/${mode}.tlist`;
  const dict = await StsDict.load(url);
  const regexLine = /\n|\r\n?/;
  const regexSep = /[ \t]+/;
  if (customDict) {
    for (const line of customDict.split(regexLine)) {
      const [key, ...values] = line.split(regexSep);
      if (!key) { continue; }
      if (values.length) {
        dict.add(key, values, true);
      } else {
        dict.delete(key);
      }
    }
  }

  // save cache
  loadDict.lastDict = dict;
  dictInfo.set(dict, {mode, customDict});

  return dict;
}

function convertText(dict, text, exclude) {
  const timeStart = performance.now();
  const result = _convertText(dict, text, exclude);
  console.log(`convertText(chars=${text.length}, mode=${dictInfo.get(dict).mode}, customDict=${!!dictInfo.get(dict).customDict}, exclude=${exclude}): ${performance.now() - timeStart} ms`);
  return result;
}

function _convertText(dict, text, exclude) {
  const result = [];
  for (const part of dict.convert(text, parseExcludePattern(exclude))) {
    if (typeof part === 'string') {
      result.push(part);
      continue;
    }

    result.push(part.values[0]);
  }
  return result.join('');
}

function escapeHtml(...args) {
  const regex = /[&<"]/g;
  const func = m => map[m];
  const map = {
    "&": "&amp;",
    "<": "&lt;",
    '"': "&quot;",
  };

  escapeHtml = function escapeHtml(str) {
    return str.replace(regex, func);
  }

  return escapeHtml(...args);
}

function convertHtml(dict, text, exclude) {
	convertHtml.lastOptions = {dict, exclude};
  const timeStart = performance.now();
  const result = _convertHtml(dict, text, exclude);
  console.log(`convertHtml(chars=${text.length}, mode=${dictInfo.get(dict).mode}, customDict=${!!dictInfo.get(dict).customDict}, exclude=${exclude}): ${performance.now() - timeStart} ms`);
  return result;
}

function _convertHtml(dict, text, exclude) {
  const result = [];
  for (const part of dict.convert(text, parseExcludePattern(exclude))) {
    if (typeof part === 'string') {
      result.push(escapeHtml(part));
      continue;
    }
    if ('text' in part) {
      result.push(`<a>${escapeHtml(part.text)}</a>`);
      continue;
    }

    const atomic = part.key.length === 1;
    const cls = [(atomic && part.values.length <= 1) ? 'single' : 'unchecked'];
    const key = part.key.join('');
    const values = part.values;
    if (values.length && key !== values[0]) { cls.push('changed'); }

    result.push(`<a tabindex=0 class="${cls.join(' ')}">`);
    result.push(`<del hidden>${escapeHtml(key)}</del>`);
    for (let i = 0, I = values.length; i < I; i++) {
      const value = values[i];
      result.push(`<ins${i === 0 ? '' : ' hidden'}>${escapeHtml(value)}</ins>`);
    }
    result.push(`</a>`);
  }
  return result.join('');
}

async function convertFile(dict, file, method, charset, exclude) {
  let text = await readFileAsText(file, charset);
  let filename = file.name;
  if (['filename-content', 'filename'].includes(method)) {
    filename = convertText(dict, filename, exclude);
  }
  if (['filename-content', 'content'].includes(method)) {
    text = convertText(dict, text, exclude);
  }
  const fileNew = new File([text], filename, {type: 'text/plain'});
  downloadFile(fileNew);
}

async function readFileAsText(blob, charset = 'utf-8') {
  const event = await new Promise((resolve, reject) => {
    let reader = new FileReader();
    reader.onload = resolve;
    reader.onerror = reject;
    reader.readAsText(blob, charset);
  });
  return event.target.result;
}

function downloadFile(file) {
  const a = document.createElement('a');
  a.download = file.name;
  a.href = URL.createObjectURL(file);
  document.body.appendChild(a);
  a.click();
  a.remove();
}

async function showAdvancedOptions(formElem) {
  if (typeof HTMLDialogElement === 'undefined') {
    alert('瀏覽器不支援 <dialog> 對話方塊元素');
    return;
  }

  const dialog = document.getElementById('panel-options');
  const form = dialog.querySelector('form');

  for (const option of ['custom-dict', 'exclude-pattern', 'convert-file-method', 'convert-file-charset']) {
    form[option].value = formElem[option].value;
  }

  const result = await new Promise((resolve, reject) => {
    function onClose(event) {
      dialog.removeEventListener('close', onClose);
      resolve(dialog.returnValue);
    }
    dialog.addEventListener('close', onClose);
    dialog.returnValue = '';
    dialog.showModal();
  });

  if (!result) { return; }
  for (const elem of dialog.querySelectorAll('[name]')) {
    formElem[elem.name].value = elem.value;
  }
}

document.addEventListener('DOMContentLoaded', function (event) {
  const panel = document.getElementById('panel');
  const form = panel.querySelector('form');

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const dict = await loadDict(form.method.value, form['custom-dict'].value);
    const result = convertHtml(dict, form.input.value, form['exclude-pattern'].value);

    const wrapper = document.getElementById('viewer');
    wrapper.innerHTML = result;
    wrapper.hidden = false;
    wrapper.scrollIntoView();

    const a = wrapper.querySelector('a.unchecked');
    if (a) { a.focus(); }
  });

  form['input'].addEventListener('dragover', (event) => {
    event.preventDefault();  // required to allow drop
    event.dataTransfer.dropEffect = 'copy';
  });

  form['input'].addEventListener('drop', async (event) => {
    async function handleEntry(entry) {
      if (entry.isFile) {
        let file = await new Promise((resolve, reject) => {
          entry.file(resolve, reject);
        });
        const {type, lastModified} = file;
        file = new File([file], entry.fullPath.slice(1) || file.name, {type, lastModified});
        await convertFile(dict, file, method, charset, exclude);
        return;
      }

      // load all subentries into entries
      let entries = [];
      {
        const reader = entry.createReader();
        let subentries;
        do {
          subentries = await new Promise((resolve, reject) => {
            reader.readEntries(resolve, reject);
          });
          entries = entries.concat(subentries);
        } while (subentries.length)
      }

      // handle loaded entries
      for (const entry of entries) {
        await handleEntry(entry);
      }
    }

    event.preventDefault();
    const entries = Array.prototype.map.call(
      event.dataTransfer.items,
      x => x.webkitGetAsEntry && x.webkitGetAsEntry()
    );
    const mode = form.method.value;
    const exclude = form['exclude-pattern'].value;
    const customDict = form['custom-dict'].value;
    const method = form['convert-file-method'].value;
    const charset = form['convert-file-charset'].value;
    const dict = await loadDict(mode, customDict);
    for (const entry of entries) {
      await handleEntry(entry);
    }
  });

  form['copy-text'].addEventListener('click', async (event) => {
    event.preventDefault();
    const text = document.getElementById('viewer').innerText;
    try {
      await navigator.clipboard.writeText(text);
    } catch (ex) {
      console.error(ex);
    }
  });

  form['convert-file'].addEventListener('click', (event) => {
    event.preventDefault();
    form['convert-file-input'].value = null;
    form['convert-file-input'].click();
  });

  form['convert-file-input'].addEventListener('change', async (event) => {
    event.preventDefault();
    const files = Array.from(event.target.files);
    if (!(files && files.length)) { return; }
    const dict = await loadDict(form.method.value, form['custom-dict'].value);
    await convertFile(dict, files[0], form['convert-file-method'].value, form['convert-file-charset'].value, form['exclude-pattern'].value);
  });

  form.advanced.addEventListener('click', (event) => {
    event.preventDefault();
    showAdvancedOptions(form);
  });

  const dialog = document.getElementById('panel-options');
  {
    const elem = dialog.querySelector('[name="exclude-pattern"]');
    elem.addEventListener('change', (event) => {
      try {
        parseExcludePattern(elem.value);
      } catch(ex) {
        elem.setCustomValidity(ex);
        return;
      }
      elem.setCustomValidity('');
    });
  }

  const params = new URL(location).searchParams;
  {
    for (const key of [
      'input',
      'method',
      'convert-file-method',
      'convert-file-charset',
      'custom-dict',
      'exclude-pattern',
    ]) {
      const value = params.get(key);
      if (value !== null) {
        form[key].value = value;
      }
    }
    if (params.get('input') !== null) {
      form.querySelector('input[type="submit"]').click();
    }
  }
});

{%- endif %}
