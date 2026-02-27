import { writable } from 'svelte/store';

export const matchState = writable({
    round: 0,
    scoreA: 0,
    scoreB: 0,
    status: 'WAITING',
    lastRoundWinner: 'NONE',
    matchWinner: 'NONE',
    elapsed: 0
});