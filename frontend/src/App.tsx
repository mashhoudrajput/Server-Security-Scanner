import { ScanPage } from "./pages/ScanPage";

function App() {
  return (
    <div className="app">
      <header className="header">
        <span className="header-badge">Enterprise Security</span>
        <h1>Server Security Scanner</h1>
        <p className="subtitle">
          Enter host, username, key — click Scan — get full report
        </p>
      </header>
      <main className="main">
        <ScanPage />
      </main>
    </div>
  );
}

export default App;
