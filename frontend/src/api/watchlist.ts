import apiClient from './client';

export interface WatchlistItem {
    id: number;
    user_id: number;
    stock_code: string;
    stock_name?: string;
    created_at: string;
}

export interface WatchlistStatus {
    is_favorite: boolean;
}

export const watchlistAPI = {
    /**
     * 获取自选股列表
     */
    getWatchlist: async () => {
        const response = await apiClient.get<WatchlistItem[]>('/api/watchlist');
        return response.data;
    },

    /**
     * 添加到自选股
     */
    addToWatchlist: async (stockCode: string) => {
        const response = await apiClient.post('/api/watchlist', { stock_code: stockCode });
        return response.data;
    },

    /**
     * 从自选股移除
     */
    removeFromWatchlist: async (stockCode: string) => {
        const response = await apiClient.delete(`/api/watchlist/${stockCode}`);
        return response.data;
    },

    /**
     * 检查是否在自选股中
     */
    checkStatus: async (stockCode: string) => {
        const response = await apiClient.get<WatchlistStatus>(`/api/watchlist/${stockCode}/status`);
        return response.data;
    }
};
