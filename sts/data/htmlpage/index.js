function moveAnchor(anchor, offset, filter) {
  const viewer = document.querySelector('#viewer');
  const anchors = viewer.querySelectorAll('a');
  const len = anchors.length;

  // no anchor, it's impossible to move
  if (len === 0) {
    return false;
  }

  let idx = Array.prototype.indexOf.call(anchors, anchor);

  if (idx === -1) {
    throw new Error(`specified anchor is invalid`);
  }

  let anchorNew;
  while (true) {
    idx += offset;
    while (idx >= len) { idx -= len; }
    while (idx < 0) { idx += len; }
    anchorNew = anchors[idx];
    if (anchorNew === anchor) {
      return false;
    }
    if (typeof filter !== "function" || filter(anchorNew)) {
      break;
    }
  }
  return anchorNew;
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
  const anchors = viewer.querySelectorAll('a:not(.unmatched)');
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
  };

  if (typeof cmd === 'undefined') {
    if (typeof HTMLDialogElement !== 'undefined') {
      const dialog = document.createElement('dialog');
      const form = dialog.appendChild(document.createElement('form'));
      form.method = 'dialog';
      const header = form.appendChild(document.createElement('header'));
      header.textContent = '請選擇要執行的指令：';
      const section = form.appendChild(document.createElement('section'));
      const footer = form.appendChild(document.createElement('footer'));
      const submitBtn = footer.appendChild(document.createElement('input'));
      submitBtn.type = 'submit';
      submitBtn.value = '確認';
      const cancelBtn = footer.appendChild(document.createElement('input'));
      cancelBtn.type = 'button';
      cancelBtn.value = '取消';
      cancelBtn.addEventListener('click', (event) => {
        dialog.close('');
      });
      for (const cmd in cmds) {
        const label = section.appendChild(document.createElement('label'));
        const input = label.appendChild(document.createElement('input'));
        input.type = 'radio';
        input.name = 'cmd';
        input.value = cmd;
        label.appendChild(document.createTextNode(cmds[cmd]));
      }

      const target = runCommand.lastCmd ?
          section.querySelector(`input[value="${CSS.escape(runCommand.lastCmd)}"]`) :
          section.querySelector('input');
      target.checked = true;
      target.autofocus = true;

      cmd = await new Promise((resolve, reject) => {
        dialog.addEventListener('close', (event) => {
          const rv = dialog.returnValue ? dialog.querySelector('form').cmd.value : null;
          resolve(rv);
        });
        document.body.appendChild(dialog);
        dialog.showModal();
      });
      dialog.remove();
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
  }

  runCommand.lastCmd = cmd;
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

  if (target.matches('.editing') && event.key !== "`") {
    return;
  }

  if (event.shiftKey || event.ctrlKey || event.altKey || event.metaKey) {
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
    const cls = (atomic && elem.querySelectorAll('ins').length <= 1) ? 'single' : 'unchecked';
    elem.classList.add(cls);
  }

  const target = viewer.querySelector('a.unchecked');
  if (target) { target.focus(); }
});
