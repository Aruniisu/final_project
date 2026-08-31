import React from 'react';

const DashboardSkeleton = () => {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Header Skeleton */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-2">
          <div className="h-8 w-48 bg-slate-200 dark:bg-slate-700 rounded"></div>
          <div className="h-4 w-64 bg-slate-200 dark:bg-slate-700 rounded"></div>
        </div>
        <div className="flex items-center gap-3">
          <div className="h-10 w-24 bg-slate-200 dark:bg-slate-700 rounded-xl"></div>
          <div className="h-10 w-32 bg-slate-200 dark:bg-slate-700 rounded-xl"></div>
        </div>
      </div>

      {/* Stats Grid Skeleton */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="glass-card p-6">
            <div className="flex items-start justify-between">
              <div className="space-y-2 flex-1">
                <div className="h-4 w-24 bg-slate-200 dark:bg-slate-700 rounded"></div>
                <div className="h-8 w-20 bg-slate-200 dark:bg-slate-700 rounded"></div>
                <div className="h-3 w-16 bg-slate-200 dark:bg-slate-700 rounded"></div>
              </div>
              <div className="h-12 w-12 bg-slate-200 dark:bg-slate-700 rounded-xl"></div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-card p-6 h-80">
          <div className="h-6 w-32 bg-slate-200 dark:bg-slate-700 rounded mb-4"></div>
          <div className="h-56 bg-slate-200 dark:bg-slate-700 rounded"></div>
        </div>
        <div className="glass-card p-6 h-80">
          <div className="h-6 w-32 bg-slate-200 dark:bg-slate-700 rounded mb-4"></div>
          <div className="h-56 bg-slate-200 dark:bg-slate-700 rounded-full"></div>
        </div>
      </div>

      {/* Quick Actions & Activity Skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-card p-6 h-64">
          <div className="h-6 w-32 bg-slate-200 dark:bg-slate-700 rounded mb-4"></div>
          <div className="grid grid-cols-2 gap-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-14 bg-slate-200 dark:bg-slate-700 rounded-xl"></div>
            ))}
          </div>
        </div>
        <div className="glass-card p-6 h-64">
          <div className="h-6 w-32 bg-slate-200 dark:bg-slate-700 rounded mb-4"></div>
          <div className="space-y-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="h-8 w-8 bg-slate-200 dark:bg-slate-700 rounded-lg"></div>
                <div className="flex-1 space-y-1">
                  <div className="h-4 w-48 bg-slate-200 dark:bg-slate-700 rounded"></div>
                  <div className="h-3 w-32 bg-slate-200 dark:bg-slate-700 rounded"></div>
                </div>
                <div className="h-6 w-16 bg-slate-200 dark:bg-slate-700 rounded-full"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardSkeleton;