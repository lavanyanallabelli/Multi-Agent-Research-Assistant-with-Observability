import os

file_path = r"d:\AI_folder\multi-agent\dashboard\index.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

logs_old = """            useEffect(() => {
                if (endRef.current) endRef.current.scrollIntoView({ behavior: 'smooth' });
            }, [logs]);"""
logs_new = """            useEffect(() => {
                if (endRef.current) {
                    const container = endRef.current.parentElement;
                    container.scrollTop = container.scrollHeight;
                }
            }, [logs]);"""

if logs_old in content:
    content = content.replace(logs_old, logs_new)
elif logs_old.replace('\n', '\r\n') in content:
    content = content.replace(logs_old.replace('\n', '\r\n'), logs_new)

app_old = """        function App() {
            const [page, setPage] = useState("overview");
            const { data: stateData, reload: reloadState } = useAsyncData(() => fetchApi("/api/trading/state"), [], 10000);"""
app_new = """        function App() {
            const [page, setPage] = useState("overview");
            const { data: stateData, reload: reloadState } = useAsyncData(() => fetchApi("/api/trading/state"), [], 10000);
            const scrollRef = useRef(null);

            useEffect(() => {
                if (scrollRef.current) {
                    scrollRef.current.scrollTop = 0;
                }
            }, [page]);"""

if app_old in content:
    content = content.replace(app_old, app_new)
elif app_old.replace('\n', '\r\n') in content:
    content = content.replace(app_old.replace('\n', '\r\n'), app_new)

render_old = """<div className="absolute inset-0 overflow-y-auto p-4 md:p-8 pb-32 z-10">"""
render_new = """<div ref={scrollRef} className="absolute inset-0 overflow-y-auto p-4 md:p-8 pb-32 z-10">"""

if render_old in content:
    content = content.replace(render_old, render_new)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Scroll logic patched.")
