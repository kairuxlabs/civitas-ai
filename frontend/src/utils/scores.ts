import type { CityScore } from '../types'

export function averageOverallScore(scores: CityScore[] | undefined): number | null {
  if (!scores?.length) return null
  return Math.round(scores.reduce((sum, score) => sum + score.overall_score, 0) / scores.length)
}
