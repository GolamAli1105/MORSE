export function Divider() {
  return (
    <div className="relative my-8">
      <div className="absolute inset-0 flex items-center">
        <div className="w-full border-t border-slate-600"></div>
      </div>
      <div className="relative flex justify-center text-sm">
        <span className="px-4 bg-slate-800 text-slate-400 font-medium">OR</span>
      </div>
    </div>
  );
}
