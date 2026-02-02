import React, { useState, useMemo } from 'react';
import { ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react';

// Generic types for the data table
interface Column<T> {
  key: keyof T;
  label: string;
  sortable?: boolean;
  render?: (value: T[keyof T], row: T) => React.ReactNode;
}

type SortDirection = 'asc' | 'desc' | null;

interface SortConfig<T> {
  key: keyof T | null;
  direction: SortDirection;
}

interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  defaultPageSize?: number;
}

// Sample data type
interface Employee {
  id: number;
  name: string;
  department: string;
  position: string;
  salary: number;
  startDate: string;
  email: string;
  status: 'Active' | 'On Leave' | 'Inactive';
}

// Main DataTable component
function DataTable<T extends Record<string, any>>({ 
  data, 
  columns,
  defaultPageSize = 10 
}: DataTableProps<T>) {
  const [sortConfig, setSortConfig] = useState<SortConfig<T>>({ 
    key: null, 
    direction: null 
  });
  const [filterText, setFilterText] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(defaultPageSize);

  const isDate = (v: unknown): v is Date =>
    typeof v === "object" && v !== null && v instanceof Date;
  

  // Sorting logic
  const sortedData = useMemo(() => {
    const sorted = [...data];
    
    if (sortConfig.key && sortConfig.direction) {
      sorted.sort((a, b) => {
        const aValue = a[sortConfig.key!];
        const bValue = b[sortConfig.key!];

        // Handle different data types
        let comparison = 0;
        
        if (typeof aValue === 'number' && typeof bValue === 'number') {
          comparison = aValue - bValue;
        } else if (typeof aValue === 'string' && typeof bValue === 'string') {
          comparison = aValue.toLowerCase().localeCompare(bValue.toLowerCase());
        } else if (isDate(aValue) && isDate(bValue)) {
          comparison = aValue.getTime() - bValue.getTime();
        } else {
          // Fallback to string comparison
          comparison = String(aValue).localeCompare(String(bValue));
        }

        return sortConfig.direction === 'asc' ? comparison : -comparison;
      });
    }
    
    return sorted;
  }, [data, sortConfig]);

  // Filtering logic
  const filteredData = useMemo(() => {
    if (!filterText) return sortedData;
    
    return sortedData.filter(row => {
      return Object.values(row).some(value => {
        if (value === null || value === undefined) return false;
        return String(value).toLowerCase().includes(filterText.toLowerCase());
      });
    });
  }, [sortedData, filterText]);

  // Pagination logic
  const totalPages = Math.ceil(filteredData.length / pageSize);
  const paginatedData = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    return filteredData.slice(startIndex, startIndex + pageSize);
  }, [filteredData, currentPage, pageSize]);

  // Handle sort
  const handleSort = (key: keyof T) => {
    const column = columns.find(col => col.key === key);
    if (!column?.sortable && column?.sortable !== undefined) return;

    let direction: SortDirection = 'asc';
    
    if (sortConfig.key === key) {
      if (sortConfig.direction === 'asc') {
        direction = 'desc';
      } else if (sortConfig.direction === 'desc') {
        direction = null;
      }
    }
    
    setSortConfig({ key: direction ? key : null, direction });
  };

  // Handle filter change
  const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFilterText(e.target.value);
    setCurrentPage(1); // Reset to first page on filter
  };

  // Handle page size change
  const handlePageSizeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setPageSize(Number(e.target.value));
    setCurrentPage(1); // Reset to first page
  };

  // Render sort icon
  const renderSortIcon = (key: keyof T) => {
    if (sortConfig.key !== key) {
      return <ChevronsUpDown className="w-4 h-4 text-gray-400" />;
    }
    if (sortConfig.direction === 'asc') {
      return <ChevronUp className="w-4 h-4 text-blue-600" />;
    }
    return <ChevronDown className="w-4 h-4 text-blue-600" />;
  };

  // Calculate pagination info
  const startItem = filteredData.length === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, filteredData.length);

  return (
    <div className="w-full max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Data Table</h1>
        <p className="text-gray-600">Sortable, filterable, and paginated data view</p>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-4">
        <div className="p-4 flex flex-wrap gap-4 items-center justify-between">
          {/* Search filter */}
          <div className="flex-1 min-w-64">
            <input
              type="text"
              placeholder="Search across all columns..."
              value={filterText}
              onChange={handleFilterChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            />
          </div>

          {/* Page size selector */}
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-700 font-medium">
              Rows per page:
            </label>
            <select
              value={pageSize}
              onChange={handlePageSizeChange}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {columns.map((column) => (
                  <th
                    key={String(column.key)}
                    onClick={() => handleSort(column.key)}
                    className={`px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider ${
                      (column.sortable !== false) ? 'cursor-pointer select-none hover:bg-gray-100' : ''
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span>{column.label}</span>
                      {column.sortable !== false && renderSortIcon(column.key)}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {paginatedData.length === 0 ? (
                <tr>
                  <td
                    colSpan={columns.length}
                    className="px-6 py-12 text-center text-gray-500"
                  >
                    {filterText ? `No results found for "${filterText}"` : 'No data available'}
                  </td>
                </tr>
              ) : (
                paginatedData.map((row, rowIndex) => (
                  <tr
                    key={rowIndex}
                    className="hover:bg-gray-50 transition-colors"
                  >
                    {columns.map((column) => (
                      <td
                        key={String(column.key)}
                        className="px-6 py-4 text-sm text-gray-900"
                      >
                        {column.render
                          ? column.render(row[column.key], row)
                          : String(row[column.key])}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {filteredData.length > 0 && (
          <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
            <div className="text-sm text-gray-700">
              Showing <span className="font-medium">{startItem}</span> to{' '}
              <span className="font-medium">{endItem}</span> of{' '}
              <span className="font-medium">{filteredData.length}</span> results
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Previous
              </button>

              <div className="flex gap-1">
                {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
                  let pageNum;
                  if (totalPages <= 7) {
                    pageNum = i + 1;
                  } else if (currentPage <= 4) {
                    pageNum = i + 1;
                  } else if (currentPage >= totalPages - 3) {
                    pageNum = totalPages - 6 + i;
                  } else {
                    pageNum = currentPage - 3 + i;
                  }

                  return (
                    <button
                      key={pageNum}
                      onClick={() => setCurrentPage(pageNum)}
                      className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                        currentPage === pageNum
                          ? 'bg-blue-600 text-white'
                          : 'text-gray-700 bg-white border border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
              </div>

              <button
                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Sample data (25 employees)
const sampleData: Employee[] = [
  { id: 1, name: 'Alice Johnson', department: 'Engineering', position: 'Senior Developer', salary: 95000, startDate: '2020-03-15', email: 'alice.j@company.com', status: 'Active' },
  { id: 2, name: 'Bob Smith', department: 'Marketing', position: 'Marketing Manager', salary: 78000, startDate: '2019-07-22', email: 'bob.s@company.com', status: 'Active' },
  { id: 3, name: 'Carol White', department: 'HR', position: 'HR Director', salary: 89000, startDate: '2018-01-10', email: 'carol.w@company.com', status: 'Active' },
  { id: 4, name: 'David Brown', department: 'Engineering', position: 'Junior Developer', salary: 62000, startDate: '2022-05-01', email: 'david.b@company.com', status: 'Active' },
  { id: 5, name: 'Emma Davis', department: 'Sales', position: 'Sales Representative', salary: 55000, startDate: '2021-09-14', email: 'emma.d@company.com', status: 'On Leave' },
  { id: 6, name: 'Frank Wilson', department: 'Engineering', position: 'Tech Lead', salary: 110000, startDate: '2017-11-30', email: 'frank.w@company.com', status: 'Active' },
  { id: 7, name: 'Grace Lee', department: 'Finance', position: 'Financial Analyst', salary: 72000, startDate: '2020-08-19', email: 'grace.l@company.com', status: 'Active' },
  { id: 8, name: 'Henry Martinez', department: 'Operations', position: 'Operations Manager', salary: 85000, startDate: '2019-04-05', email: 'henry.m@company.com', status: 'Active' },
  { id: 9, name: 'Ivy Taylor', department: 'Design', position: 'UX Designer', salary: 68000, startDate: '2021-02-28', email: 'ivy.t@company.com', status: 'Active' },
  { id: 10, name: 'Jack Anderson', department: 'Engineering', position: 'DevOps Engineer', salary: 92000, startDate: '2020-10-12', email: 'jack.a@company.com', status: 'Inactive' },
  { id: 11, name: 'Kate Thompson', department: 'Marketing', position: 'Content Specialist', salary: 58000, startDate: '2022-01-20', email: 'kate.t@company.com', status: 'Active' },
  { id: 12, name: 'Leo Garcia', department: 'Sales', position: 'Sales Manager', salary: 82000, startDate: '2018-06-08', email: 'leo.g@company.com', status: 'Active' },
  { id: 13, name: 'Mia Rodriguez', department: 'HR', position: 'Recruiter', salary: 61000, startDate: '2021-11-03', email: 'mia.r@company.com', status: 'Active' },
  { id: 14, name: 'Noah Clark', department: 'Engineering', position: 'Software Architect', salary: 125000, startDate: '2016-09-15', email: 'noah.c@company.com', status: 'Active' },
  { id: 15, name: 'Olivia Lewis', department: 'Finance', position: 'Accountant', salary: 65000, startDate: '2020-12-01', email: 'olivia.l@company.com', status: 'Active' },
  { id: 16, name: 'Paul Walker', department: 'Design', position: 'Senior Designer', salary: 76000, startDate: '2019-03-17', email: 'paul.w@company.com', status: 'Active' },
  { id: 17, name: 'Quinn Hall', department: 'Operations', position: 'Logistics Coordinator', salary: 54000, startDate: '2022-07-09', email: 'quinn.h@company.com', status: 'On Leave' },
  { id: 18, name: 'Rachel Allen', department: 'Marketing', position: 'SEO Specialist', salary: 63000, startDate: '2021-04-22', email: 'rachel.a@company.com', status: 'Active' },
  { id: 19, name: 'Sam Young', department: 'Engineering', position: 'QA Engineer', salary: 71000, startDate: '2020-06-30', email: 'sam.y@company.com', status: 'Active' },
  { id: 20, name: 'Tina King', department: 'Sales', position: 'Account Executive', salary: 67000, startDate: '2019-12-05', email: 'tina.k@company.com', status: 'Active' },
  { id: 21, name: 'Uma Scott', department: 'HR', position: 'HR Coordinator', salary: 52000, startDate: '2022-09-18', email: 'uma.s@company.com', status: 'Active' },
  { id: 22, name: 'Victor Green', department: 'Finance', position: 'Finance Manager', salary: 94000, startDate: '2018-08-24', email: 'victor.g@company.com', status: 'Active' },
  { id: 23, name: 'Wendy Adams', department: 'Design', position: 'UI Designer', salary: 69000, startDate: '2021-06-11', email: 'wendy.a@company.com', status: 'Inactive' },
  { id: 24, name: 'Xavier Baker', department: 'Operations', position: 'Supply Chain Analyst', salary: 66000, startDate: '2020-02-14', email: 'xavier.b@company.com', status: 'Active' },
  { id: 25, name: 'Yara Nelson', department: 'Engineering', position: 'Full Stack Developer', salary: 88000, startDate: '2021-08-07', email: 'yara.n@company.com', status: 'Active' },
];

// Column configuration
const columns: Column<Employee>[] = [
  { key: 'id', label: 'ID', sortable: true },
  { key: 'name', label: 'Name', sortable: true },
  { key: 'department', label: 'Department', sortable: true },
  { key: 'position', label: 'Position', sortable: true },
  { 
    key: 'salary', 
    label: 'Salary', 
    sortable: true,
    render: (value) => `$${Number(value).toLocaleString()}`
  },
  { key: 'startDate', label: 'Start Date', sortable: true },
  { key: 'email', label: 'Email', sortable: false },
  { 
    key: 'status', 
    label: 'Status', 
    sortable: true,
    render: (value) => {
      const colors = {
        'Active': 'bg-green-100 text-green-800',
        'On Leave': 'bg-yellow-100 text-yellow-800',
        'Inactive': 'bg-gray-100 text-gray-800'
      };
      return (
        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${colors[value as keyof typeof colors]}`}>
          {String(value)}
        </span>
      );
    }
  },
];

// App component
export default function App() {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <DataTable data={sampleData} columns={columns} defaultPageSize={10} />
    </div>
  );
}