import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { TrainingCenterPage } from './TrainingCenter/TrainingCenterPage'
import { GradingResultsPage } from './GradingResults/GradingResultsPage'
import { ErrorReinforcementPage } from './ErrorReinforcement/ErrorReinforcementPage'
import { LearningPlanPage } from './LearningPlan/LearningPlanPage'
import { SocialLearningPage } from './SocialLearning/SocialLearningPage'

export const StudentPages: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/student/training" replace />} />
      <Route path="/training" element={<TrainingCenterPage />} />
      <Route path="/grading" element={<GradingResultsPage />} />
      <Route path="/errors" element={<ErrorReinforcementPage />} />
      <Route path="/plan" element={<LearningPlanPage />} />
      <Route path="/social" element={<SocialLearningPage />} />
    </Routes>
  )
}
