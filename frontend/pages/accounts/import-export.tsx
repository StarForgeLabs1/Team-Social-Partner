import { useRef } from "react";

export default function AccountImportExport() {
  const fileInput = useRef<HTMLInputElement>(null);

  const handleImport = async () => {
    const file = fileInput.current?.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    await fetch("/api/accounts/import", {method: "POST", body: formData});
    alert("导入完成");
  };

  const handleExport = async () => {
    const res = await fetch("/api/accounts/export");
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "accounts.csv";
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div>
      <h2>批量导入/导出账号</h2>
      <input type="file" ref={fileInput} accept=".csv" />
      <button onClick={handleImport}>导入CSV</button>
      <button onClick={handleExport}>导出CSV</button>
    </div>
  );
}