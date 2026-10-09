interface ConsoleProps {
  output: string;
  isError: boolean;
}

export default function Console({ output, isError }: ConsoleProps) {
  return (
    <div className="h-full overflow-auto bg-[#1e1e2e] p-3 font-mono text-sm rounded-lg">
      <pre className={`whitespace-pre-wrap ${isError ? "text-red-400" : "text-green-300"}`}>
        {output || ">>"}
      </pre>
    </div>
  );
}
