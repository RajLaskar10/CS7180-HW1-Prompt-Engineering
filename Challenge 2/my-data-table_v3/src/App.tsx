import React, { useState, useMemo, useEffect } from 'react';

// Types
type SortDirection = 'asc' | 'desc' | null;

interface SortConfig {
  key: string;
  direction: SortDirection;
}

interface TableRow {
  id: number;
  name: string;
  email: string;
  age: number;
  joinDate: string;
  status: 'active' | 'inactive' | 'pending';
}

interface Column {
  key: keyof TableRow;
  label: string;
  sortable: boolean;
}

// Generate sample data
const generateSampleData = (): TableRow[] => {
  const firstNames = ['James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda', 'William', 'Elizabeth', 'David', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica', 'Thomas', 'Sarah', 'Charles', 'Karen'];
  const lastNames = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin'];
  const statuses: Array<'active' | 'inactive' | 'pending'> = ['active', 'inactive', 'pending'];
  
  const data: TableRow[] = [];
  
  for (let i = 1; i <= 50; i++) {
    const firstName = firstNames[Math.floor(Math.random() * firstNames.length)];
    const lastName = lastNames[Math.floor(Math.random() * lastNames.length)];
    const name = `${firstName} ${lastName}`;
    const email = `${firstName.toLowerCase()}.${lastName.toLowerCase()}${i}@example.com`;
    const age = Math.floor(Math.random() * 43) + 18; // 18-60
    const joinDate = new Date(2020 + Math.floor(Math.random() * 5), Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1).toISOString().split('T')[0];
    const status = statuses[Math.floor(Math.random() * statuses.length)];
    
    data.push({ id: i, name, email, age, joinDate, status });
  }
  
  return data;
};

// Custom hook for debounced value
const useDebounce = <T,>(value: T, delay: number): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};

// Main DataTable Component
const DataTable: React.FC = () => {
  const [data] = useState<TableRow[]>(generateSampleData());
  const [sortConfig, setSortConfig] = useState<SortConfig>({ key: '', direction: null });
  const [filterText, setFilterText] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Debounce the filter text
  const debouncedFilterText = useDebounce(filterText, 300);

  // Column configuration
  const columns: Column[] = [
    { key: 'id', label: 'ID', sortable: true },
    { key: 'name', label: 'Name', sortable: true },
    { key: 'email', label: 'Email', sortable: true },
    { key: 'age', label: 'Age', sortable: true },
    { key: 'joinDate', label: 'Join Date', sortable: true },
    { key: 'status', label: 'Status', sortable: true },
  ];

  // Sorting logic
  const sortedData = useMemo(() => {
    if (!sortConfig.direction) return data;

    const sorted = [...data].sort((a, b) => {
      const aValue = a[sortConfig.key as keyof TableRow];
      const bValue = b[sortConfig.key as keyof TableRow];

      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue;
      }

      if (sortConfig.key === 'joinDate') {
        const aDate = new Date(aValue as string).getTime();
        const bDate = new Date(bValue as string).getTime();
        return sortConfig.direction === 'asc' ? aDate - bDate : bDate - aDate;
      }

      const aStr = String(aValue).toLowerCase();
      const bStr = String(bValue).toLowerCase();
      
      if (sortConfig.direction === 'asc') {
        return aStr < bStr ? -1 : aStr > bStr ? 1 : 0;
      } else {
        return aStr > bStr ? -1 : aStr < bStr ? 1 : 0;
      }
    });

    return sorted;
  }, [data, sortConfig]);

  // Filtering logic
  const filteredData = useMemo(() => {
    if (!debouncedFilterText) return sortedData;

    return sortedData.filter(row => {
      return Object.values(row).some(value => {
        return String(value).toLowerCase().includes(debouncedFilterText.toLowerCase());
      });
    });
  }, [sortedData, debouncedFilterText]);

  // Pagination logic
  const totalPages = Math.ceil(filteredData.length / pageSize);
  const paginatedData = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    return filteredData.slice(startIndex, startIndex + pageSize);
  }, [filteredData, currentPage, pageSize]);

  // Handle sort
  const handleSort = (key: string) => {
    let direction: SortDirection = 'asc';

    if (sortConfig.key === key) {
      if (sortConfig.direction === 'asc') {
        direction = 'desc';
      } else if (sortConfig.direction === 'desc') {
        direction = null;
      }
    }

    setSortConfig({ key, direction });
  };

  // Handle filter change
  const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFilterText(e.target.value);
    setCurrentPage(1);
  };

  // Handle page size change
  const handlePageSizeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setPageSize(Number(e.target.value));
    setCurrentPage(1);
  };

  // Pagination handlers
  const goToFirstPage = () => setCurrentPage(1);
  const goToLastPage = () => setCurrentPage(totalPages);
  const goToPreviousPage = () => setCurrentPage(prev => Math.max(1, prev - 1));
  const goToNextPage = () => setCurrentPage(prev => Math.min(totalPages, prev + 1));

  // Sort icon component
  const SortIcon: React.FC<{ columnKey: string }> = ({ columnKey }) => {
    if (sortConfig.key !== columnKey) {
      return <span style={styles.sortIcon}>⇅</span>;
    }
    if (sortConfig.direction === 'asc') {
      return <span style={styles.sortIconActive}>↑</span>;
    }
    if (sortConfig.direction === 'desc') {
      return <span style={styles.sortIconActive}>↓</span>;
    }
    return <span style={styles.sortIcon}>⇅</span>;
  };

  // Status badge component
  const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
    const statusStyles = {
      active: { ...styles.badge, backgroundColor: '#d1fae5', color: '#065f46' },
      inactive: { ...styles.badge, backgroundColor: '#fee2e2', color: '#991b1b' },
      pending: { ...styles.badge, backgroundColor: '#fef3c7', color: '#92400e' },
    };

    return (
      <span style={statusStyles[status as keyof typeof statusStyles]}>
        {status}
      </span>
    );
  };

  // Calculate display info
  const startItem = filteredData.length === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, filteredData.length);
  const showPagination = totalPages > 1;

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>Employee Directory</h1>
        <p style={styles.subtitle}>Manage and view employee information</p>
      </div>

      {/* Controls */}
      <div style={styles.controls}>
        <div style={styles.searchContainer}>
          <input
            type="text"
            placeholder="Search across all columns..."
            value={filterText}
            onChange={handleFilterChange}
            style={styles.searchInput}
          />
          {filterText && (
            <span style={styles.searchHint}>
              {filteredData.length} result{filteredData.length !== 1 ? 's' : ''} found
            </span>
          )}
        </div>

        <div style={styles.pageSizeContainer}>
          <label style={styles.label}>Rows per page:</label>
          <select
            value={pageSize}
            onChange={handlePageSizeChange}
            style={styles.select}
          >
            <option value={5}>5</option>
            <option value={10}>10</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div style={styles.tableContainer}>
        <table style={styles.table}>
          <thead>
            <tr style={styles.headerRow}>
              {columns.map(column => (
                <th
                  key={column.key}
                  onClick={() => column.sortable && handleSort(column.key)}
                  style={{
                    ...styles.th,
                    ...(column.sortable ? styles.sortable : {}),
                  }}
                >
                  <div style={styles.thContent}>
                    {column.label}
                    {column.sortable && <SortIcon columnKey={column.key} />}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginatedData.length === 0 ? (
              <tr>
                <td colSpan={columns.length} style={styles.noResults}>
                  {debouncedFilterText ? (
                    <>
                      <div style={styles.noResultsIcon}>🔍</div>
                      <div>No results found for "{debouncedFilterText}"</div>
                      <div style={styles.noResultsHint}>Try adjusting your search terms</div>
                    </>
                  ) : (
                    <>
                      <div style={styles.noResultsIcon}>📋</div>
                      <div>No data available</div>
                    </>
                  )}
                </td>
              </tr>
            ) : (
              paginatedData.map((row, index) => (
                <tr
                  key={row.id}
                  style={{
                    ...styles.tr,
                    backgroundColor: index % 2 === 0 ? '#ffffff' : '#f9fafb',
                  }}
                >
                  <td style={styles.td}>{row.id}</td>
                  <td style={styles.td}>{row.name}</td>
                  <td style={{...styles.td, ...styles.emailCell}}>{row.email}</td>
                  <td style={styles.td}>{row.age}</td>
                  <td style={styles.td}>{row.joinDate}</td>
                  <td style={styles.td}>
                    <StatusBadge status={row.status} />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {showPagination && filteredData.length > 0 && (
        <div style={styles.pagination}>
          <div style={styles.paginationInfo}>
            Showing {startItem} to {endItem} of {filteredData.length} results
          </div>

          <div style={styles.paginationButtons}>
            <button
              onClick={goToFirstPage}
              disabled={currentPage === 1}
              style={{
                ...styles.button,
                ...(currentPage === 1 ? styles.buttonDisabled : {}),
              }}
            >
              First
            </button>
            <button
              onClick={goToPreviousPage}
              disabled={currentPage === 1}
              style={{
                ...styles.button,
                ...(currentPage === 1 ? styles.buttonDisabled : {}),
              }}
            >
              Previous
            </button>
            <span style={styles.pageIndicator}>
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={goToNextPage}
              disabled={currentPage === totalPages}
              style={{
                ...styles.button,
                ...(currentPage === totalPages ? styles.buttonDisabled : {}),
              }}
            >
              Next
            </button>
            <button
              onClick={goToLastPage}
              disabled={currentPage === totalPages}
              style={{
                ...styles.button,
                ...(currentPage === totalPages ? styles.buttonDisabled : {}),
              }}
            >
              Last
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// Styles
const styles: { [key: string]: React.CSSProperties } = {
  container: {
    maxWidth: '1400px',
    margin: '0 auto',
    padding: '24px',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  },
  header: {
    marginBottom: '32px',
  },
  title: {
    fontSize: '28px',
    fontWeight: 'bold',
    color: '#111827',
    margin: '0 0 8px 0',
  },
  subtitle: {
    fontSize: '16px',
    color: '#6b7280',
    margin: 0,
  },
  controls: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '20px',
    gap: '16px',
    flexWrap: 'wrap',
  },
  searchContainer: {
    flex: '1',
    minWidth: '280px',
  },
  searchInput: {
    width: '100%',
    padding: '10px 14px',
    fontSize: '14px',
    border: '1px solid #d1d5db',
    borderRadius: '6px',
    outline: 'none',
    transition: 'border-color 0.2s, box-shadow 0.2s',
  },
  searchHint: {
    display: 'block',
    fontSize: '12px',
    color: '#6b7280',
    marginTop: '6px',
  },
  pageSizeContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  label: {
    fontSize: '14px',
    color: '#374151',
    fontWeight: '500',
  },
  select: {
    padding: '8px 32px 8px 12px',
    fontSize: '14px',
    border: '1px solid #d1d5db',
    borderRadius: '6px',
    backgroundColor: 'white',
    cursor: 'pointer',
    outline: 'none',
  },
  tableContainer: {
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
    overflow: 'hidden',
    border: '1px solid #e5e7eb',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  headerRow: {
    backgroundColor: '#f9fafb',
    borderBottom: '2px solid #e5e7eb',
  },
  th: {
    padding: '14px 16px',
    textAlign: 'left',
    fontSize: '13px',
    fontWeight: '600',
    color: '#374151',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  sortable: {
    cursor: 'pointer',
    userSelect: 'none',
    transition: 'background-color 0.2s',
  },
  thContent: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  sortIcon: {
    fontSize: '14px',
    color: '#9ca3af',
    opacity: 0.6,
  },
  sortIconActive: {
    fontSize: '14px',
    color: '#3b82f6',
    fontWeight: 'bold',
  },
  tr: {
    transition: 'background-color 0.15s',
    cursor: 'default',
  },
  td: {
    padding: '14px 16px',
    fontSize: '14px',
    color: '#1f2937',
    borderBottom: '1px solid #f3f4f6',
  },
  emailCell: {
    maxWidth: '250px',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  badge: {
    padding: '4px 10px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: '600',
    display: 'inline-block',
  },
  noResults: {
    padding: '60px 20px',
    textAlign: 'center',
    color: '#6b7280',
    fontSize: '15px',
  },
  noResultsIcon: {
    fontSize: '48px',
    marginBottom: '16px',
  },
  noResultsHint: {
    fontSize: '13px',
    color: '#9ca3af',
    marginTop: '8px',
  },
  pagination: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: '20px',
    padding: '16px 0',
    gap: '16px',
    flexWrap: 'wrap',
  },
  paginationInfo: {
    fontSize: '14px',
    color: '#6b7280',
  },
  paginationButtons: {
    display: 'flex',
    gap: '8px',
    alignItems: 'center',
  },
  button: {
    padding: '8px 16px',
    fontSize: '14px',
    fontWeight: '500',
    color: '#374151',
    backgroundColor: 'white',
    border: '1px solid #d1d5db',
    borderRadius: '6px',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  buttonDisabled: {
    opacity: 0.5,
    cursor: 'not-allowed',
    backgroundColor: '#f9fafb',
  },
  pageIndicator: {
    fontSize: '14px',
    fontWeight: '500',
    color: '#374151',
    padding: '0 8px',
  },
};

export default DataTable;