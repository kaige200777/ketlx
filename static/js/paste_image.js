/*
 * Attach clipboard image paste handler to a textarea or contenteditable element.
 * When user pastes an image, the image blob is uploaded via /api/upload_image
 * and an <img src="url"> tag is inserted at caret position.
 */
function attachImagePaste(element) {
    if (!element) return;
    // 防止重复添加事件监听器
    if (element.dataset.imagePasteAttached === 'true') return;
    element.dataset.imagePasteAttached = 'true';
    element.addEventListener('paste', async function (e) {
        if (!e.clipboardData) return;
        const items = Array.from(e.clipboardData.items || []);
        const imgItem = items.find(it => it.kind === 'file' && it.type.startsWith('image/'));
        if (!imgItem) return; // no image in clipboard
        const file = imgItem.getAsFile();
        if (!file) return;
        e.preventDefault();
        try {
            const formData = new FormData();
            formData.append('file', file, 'pasted.' + file.type.split('/')[1]);
            const resp = await fetch('/api/upload_image', { method: 'POST', body: formData });
            const data = await resp.json();
            if (data.url) {
                insertAtCursor(element, `<img src="${data.url}"/>`);
            } else {
                alert('图片上传失败');
            }
        } catch (err) {
            console.error(err);
            alert('图片上传异常');
        }
    });
}

function insertAtCursor(textarea, text) {
    // works for textarea & input
    if (document.activeElement !== textarea) textarea.focus();
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const before = textarea.value.substring(0, start);
    const after = textarea.value.substring(end);
    textarea.value = before + text + after;
    const newPos = before.length + text.length;
    textarea.setSelectionRange(newPos, newPos);
}

// 初始化：等待 DOMReady
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('textarea.allow-img-paste').forEach(el => attachImagePaste(el));
    // 将函数暴露到全局，便于后续动态调用
    window.attachImagePaste = attachImagePaste;
}); 