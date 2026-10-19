// Small dependency-free CDP client for an explicitly supplied isolated Chrome port.
export async function connect(port) {
  if (!/^\d+$/.test(String(port))) throw new Error('Pass a numeric local Chrome debugging port.');
  const pages = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  const page = pages.find(p => p.type === 'page');
  if (!page) throw new Error('No page in isolated Chrome.');
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
  let id = 0;
  const pending = new Map();
  ws.onmessage = event => {
    const msg = JSON.parse(event.data);
    if (pending.has(msg.id)) {
      const request = pending.get(msg.id);
      clearTimeout(request.timer);
      pending.delete(msg.id);
      if (msg.error) request.reject(new Error(JSON.stringify(msg.error)));
      else request.resolve(msg.result);
    }
  };
  function send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const messageId = ++id;
      const timer = setTimeout(() => {
        pending.delete(messageId);
        reject(new Error(`CDP timeout: ${method}`));
      }, 20000);
      pending.set(messageId, { resolve, reject, timer });
      ws.send(JSON.stringify({ id: messageId, method, params }));
    });
  }
  async function evaluate(expression) {
    const result = await send('Runtime.evaluate', {
      expression, returnByValue: true, awaitPromise: true,
    });
    if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  }
  return { send, evaluate, close: () => ws.close() };
}
