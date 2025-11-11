import { Link } from 'react-router-dom';

export default function SimpleHeader() {
  return (
    <div className="bg-white rounded-2xl shadow-xl p-6">
      <div className="flex justify-between items-center flex-wrap gap-4">
        <div className="flex items-center gap-4">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
            <Link to="/">📊 Live Analyser</Link>
          </h1>
        </div>
      </div>
    </div>
  );
}
