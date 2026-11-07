import { useState } from "react";

import { getStoredUser } from "../../lib/auth";
import AgentPanel from "./AgentPanel";

export default function AgentLauncher() {
  const [open, setOpen] = useState(false);
  const user = getStoredUser();
  if (user?.role !== "admin") return null;

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-label="Mở trợ lý AI"
        title="Trợ lý AI"
        className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-emerald-500 text-2xl text-white shadow-2xl hover:bg-emerald-600"
      >
        ✦
      </button>
      {open ? <AgentPanel onClose={() => setOpen(false)} /> : null}
    </>
  );
}
