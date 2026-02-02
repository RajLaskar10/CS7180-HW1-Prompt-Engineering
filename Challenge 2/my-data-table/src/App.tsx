import React, { useState, useMemo } from 'react';
import { ChevronUp, ChevronDown, Search } from 'lucide-react';

interface User {
  id: number;
  name: string;
  email: string;
  role: string;
  status: string;
}

type SortConfig = {
  key: keyof User;
  direction: 'asc' | 'desc';
} | null;

const DataTable: React.FC = () => {
  const [data] = useState<User[]>([
    { id: 1, name: 'Alice Johnson', email: 'alice@example.com', role: 'Developer', status: 'Active' },
    { id: 2, name: 'Bob Smith', email: 'bob@example.com', role: 'Designer', status: 'Active' },
    { id: 3, name: 'Carol White', email: 'carol@example.com', role: 'Manager', status: 'Inactive' },
    { id: 4, name: 'David Brown', email: 'david@example.com', role: 'Developer', status: 'Active' },
    { id: 5, name: 'Emma Davis', email: 'emma@example.com', role: 'Designer', status: 'Active' },
    { id: 6, name: 'Frank Wilson', email: 'frank@example.com', role: 'Developer', status: 'Inactive' },
    { id: 7, name: 'Grace Lee', email: 'grace@example.com', role: 'Manager', status: 'Active' },
    { id: 8, name: 'Henry Taylor', email: 'henry@example.com', role: 'Developer', status: 'Active' },
    { id: 9, name: 'Ivy Martinez', email: 'ivy@example.com', role: 'Designer', status: 'Inactive' },
    { id: 10, name: 'Jack Anderson', email: 'jack@example.com', role: 'Developer', status: 'Active' },
    { id: 11, name: 'Kate Thompson', email: 'kate@example.com', role: 'Manager', status: 'Active' },
    { id: 12, name: 'Leo Garcia', email: 'leo@example.com', role: 'Designer', status: 'Active' },
  ]);

  const [sortConfig, setSortConfig] = useState<SortConfig>(null);
  const [filterText, setFilterText] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 5;

  const handleSort = (key: keyof User) => {
    let direction: 'asc' | 'desc' = 'asc';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const filteredData = useMemo(() => {
    return data.filter((item) =>
      Object.values(item).some((val) =>
        val.toString().toLowerCase().includes(filterText.toLowerCase())
      )
    );
  }, [data, filterText]);

  const sortedData = useMemo(() => {
    const sorted = [...filteredData];
    if (sortConfig) {
      sorted.sort((a, b) => {
        const aVal = a[sortConfig.key];
        const bVal = b[sortConfig.key];
        
        if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
        if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
      });
    }
    return sorted;
  }, [filteredData, sortConfig]);

  const totalPages = Math.ceil(sortedData.length / itemsPerPage);
  const paginatedData = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return sortedData.slice(start, start + itemsPerPage);
  }, [sortedData, currentPage]);

  const SortIcon: React.FC<{ column: keyof User }> = ({ column }) => {
    if (!sortConfig || sortConfig.key !== column) {
      return <div className="w-4 h-4" />;
    }
    return sortConfig.direction === 'asc' ? 
      <ChevronUp className="w-4 h-4" /> : 
      <ChevronDown className="w-4 h-4" />;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <div className="p-6 bg-gradient-to-r from-blue-600 to-blue-700">
            <h1 className="text-3xl font-bold text-white">User Directory</h1>
            <p className="text-blue-100 mt-1">Manage and view user information</p>
          </div>

          <div className="p-6">
            <div className="relative mb-6">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search across all columns..."
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                value={filterText}
                onChange={(e) => {
                  setFilterText(e.target.value);
                  setCurrentPage(1);
                }}
              />
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    {(['name', 'email', 'role', 'status'] as const).map((col) => (
                      <th
                        key={col}
                        className="px-6 py-4 text-left text-sm font-semibold text-gray-700 cursor-pointer hover:bg-gray-100 transition select-none"
                        onClick={() => handleSort(col)}
                      >
                        <div className="flex items-center gap-2">
                          {col.charAt(0).toUpperCase() + col.slice(1)}
                          <SortIcon column={col} />
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {paginatedData.map((user, idx) => (
                    <tr
                      key={user.id}
                      className={`border-b border-gray-100 hover:bg-blue-50 transition ${
                        idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                      }`}
                    >
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">{user.name}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{user.email}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{user.role}</td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex px-3 py-1 rounded-full text-xs font-semibold ${
                            user.status === 'Active'
                              ? 'bg-green-100 text-green-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {user.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {sortedData.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                No results found for "{filterText}"
              </div>
            )}

            {sortedData.length > 0 && (
              <div className="flex items-center justify-between mt-6 pt-6 border-t border-gray-200">
                <div className="text-sm text-gray-600">
                  Showing {((currentPage - 1) * itemsPerPage) + 1} to{' '}
                  {Math.min(currentPage * itemsPerPage, sortedData.length)} of{' '}
                  {sortedData.length} results
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition"
                  >
                    Previous
                  </button>
                  <div className="flex gap-1">
                    {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                      <button
                        key={page}
                        onClick={() => setCurrentPage(page)}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                          currentPage === page
                            ? 'bg-blue-600 text-white'
                            : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                        }`}
                      >
                        {page}
                      </button>
                    ))}
                  </div>
                  <button
                    onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                    className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataTable;