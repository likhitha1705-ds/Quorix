import { useQuery } from "@tanstack/react-query";
import { api } from "@/services/api";

export function useHealth() {
  const { data, isError, isLoading, refetch } = useQuery({
    queryKey: ["backend-health"],
    queryFn: () => api.checkHealth(),
    refetchInterval: 15000,
    retry: 1,
  });

  return {
    isOnline: !isError && !!data?.status,
    isLoading,
    appName: data?.app || "Quorix",
    refetch,
  };
}

