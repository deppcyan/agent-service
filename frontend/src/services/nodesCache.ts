import { api } from './api';
import type { NodeTypesResponse } from './nodeTypes';

interface CacheEntry {
  data: NodeTypesResponse;
  timestamp: number;
}

class NodesCacheService {
  private cache: CacheEntry | null = null;
  private readonly CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
  private loadingPromise: Promise<NodeTypesResponse> | null = null;

  /**
   * Get nodes data from cache or fetch from API
   * Multiple simultaneous calls will share the same request
   */
  async getNodeTypes(): Promise<NodeTypesResponse> {
    // If we have a valid cache entry, return it
    if (this.cache && this.isCacheValid()) {
      return this.cache.data;
    }

    // If there's already a loading request in progress, wait for it
    if (this.loadingPromise) {
      return this.loadingPromise;
    }

    // Start a new request
    this.loadingPromise = this.fetchAndCache();
    
    try {
      const result = await this.loadingPromise;
      return result;
    } finally {
      // Clear the loading promise when done
      this.loadingPromise = null;
    }
  }

  /**
   * Force refresh the cache by fetching new data
   */
  async refreshCache(): Promise<NodeTypesResponse> {
    this.cache = null;
    this.loadingPromise = null;
    return this.getNodeTypes();
  }

  /**
   * Get cached data synchronously if available and valid
   */
  getCachedData(): NodeTypesResponse | null {
    if (this.cache && this.isCacheValid()) {
      return this.cache.data;
    }
    return null;
  }

  /**
   * Check if cache is still valid
   */
  private isCacheValid(): boolean {
    if (!this.cache) return false;
    const now = Date.now();
    return (now - this.cache.timestamp) < this.CACHE_DURATION;
  }

  /**
   * Fetch data from API and update cache
   */
  private async fetchAndCache(): Promise<NodeTypesResponse> {
    try {
      const data = await api.getNodeTypes();
      this.cache = {
        data,
        timestamp: Date.now()
      };
      return data;
    } catch (error) {
      // If we have stale cache data, return it as fallback
      if (this.cache) {
        console.warn('Failed to fetch fresh nodes data, using cached data:', error);
        return this.cache.data;
      }
      throw error;
    }
  }

  /**
   * Clear the cache
   */
  clearCache(): void {
    this.cache = null;
    this.loadingPromise = null;
  }
}

// Export a singleton instance
export const nodesCache = new NodesCacheService();

// Also export the class for testing purposes
export { NodesCacheService };
