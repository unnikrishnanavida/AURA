export interface TokenUsageProps {
    totalTokens: number;
    usedTokens: number;
    remainingTokens: number;
    estimatedCost: string;
    period?: string;
}