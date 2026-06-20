import { FrictionProvider } from "../_components/FrictionMeter";
import { TopBar } from "../_components/Shell";

// Outer EHR frame: top bar + footer, shared by the patient list and every
// patient chart. The patient banner and left nav live one level down, under
// /ehr/[id], where an active patient exists.
export default function EhrLayout({ children }: { children: React.ReactNode }) {
  return (
    <FrictionProvider>
      <div className="flex h-screen flex-col bg-slate-200 text-slate-800">
        <TopBar />
        <div className="flex min-h-0 flex-1 flex-col">{children}</div>
        <footer className="flex-shrink-0 border-t border-slate-300 bg-slate-200 px-3 py-1 text-[10px] text-slate-500">
          eClinicalWorks V12 (demo mockup) · Logged in as D. Alvarez · Berkeley
          Internal Medicine Associates · Session secured
        </footer>
      </div>
    </FrictionProvider>
  );
}
