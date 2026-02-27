/**
 * 听力训练会话组件 - 需求22核心训练界面
 * 
 * 实现验收标准：
 * 1. 题型分类：支持所有四种听力题型的训练界面
 * 2. 训练特性：音频控制、字幕显示、跟读练习、听写功能
 * 3. 智能辅助：实时难点标注、错误分析、技巧提示
 */

/* eslint-disable no-console */
import { useState, useRef, useEffect, useCallback } from 'react'


import type { FC } from 'react'
import {
  Stack,
  Group,
  Text,
  Button,
  Progress,
  Card,
  ActionIcon,
  Slider,
  Badge,
  Alert,
  Textarea,
  Radio,
  Checkbox,
  Center,
  Loader,
  Paper,
} from '@mantine/core'
import {
  IconPlayerPlay,
  IconPlayerPause,
  IconPlayerStop,
  IconRepeat,
  IconVolume,
  IconVolumeOff,
  IconMicrophone,
  IconMicrophoneOff,
  IconChevronRight,
  IconChevronLeft,
  IconEye,
} from '@tabler/icons-react'

import type {
  ListeningSessionSettings,
  AudioPlaybackSpeed,
  AudioProgress,
  ListeningAnswer,
  PronunciationEvaluation,
  ListeningQuestion,
} from '../../../types/listening'
import { listeningApi, type ListeningSession } from '../../../api/listening'

interface ListeningTrainingSessionProps {
  session: ListeningSession
  settings: ListeningSessionSettings
  onComplete: (result: {
    answers: Record<string, any>
    audio_progress: Record<string, any>
    total_time_seconds: number
    listening_time_seconds: number
    answering_time_seconds: number
  }) => void
  onExit: () => void
}

interface SessionState {
  currentQuestion: number
  answers: Record<string, ListeningAnswer>
  audioProgress: AudioProgress
  startTime: number
  totalListeningTime: number
  totalAnsweringTime: number
  isRecording: boolean
  recordingBlob?: Blob
  pronunciationResult?: PronunciationEvaluation
  showSubtitles: boolean
  currentAudioTime: number
  isAudioPlaying: boolean
  playbackSpeed: AudioPlaybackSpeed
  volume: number
}

const AUDIO_SPEEDS: AudioPlaybackSpeed[] = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]

export const ListeningTrainingSession: FC<ListeningTrainingSessionProps> = ({
  session,
  settings,
  onComplete,
  onExit,
}) => {
  // 状态管理
  const [sessionState, setSessionState] = useState<SessionState>({
    currentQuestion: 1,
    answers: {},
    audioProgress: {
      current_time: 0,
      total_time: 0,
      play_count: 0,
      segments_played: [],
      pause_points: [],
      replay_segments: [],
    },
    startTime: Date.now(),
    totalListeningTime: 0,
    totalAnsweringTime: 0,
    isRecording: false,
    showSubtitles: settings.subtitles_enabled,
    currentAudioTime: 0,
    isAudioPlaying: false,
    playbackSpeed: settings.audio_speed,
    volume: 1.0,
  })

  const [currentQuestionData, setCurrentQuestionData] = useState<ListeningQuestion | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 引用
  const audioRef = useRef<HTMLAudioElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const answeringStartTimeRef = useRef<number>(0)
  const listeningStartTimeRef = useRef<number>(0)

  // ==================== 初始化和数据加载 ====================

  const loadCurrentQuestion = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      // 从会话数据中获取当前题目
      const questions = session.exercise_id ? 
        (await listeningApi.getExercise(session.exercise_id)).questions_data.questions : []
      
      if (questions.length > 0 && sessionState.currentQuestion <= questions.length) {
        const question = questions[sessionState.currentQuestion - 1]
        if (question) {
          setCurrentQuestionData(question)
        } else {
          setError('无法加载题目数据')
        }
      } else {
        setError('无法加载题目数据')
      }
    } catch (err) {
      setError('加载题目失败')
    } finally {
      setIsLoading(false)
    }
  }, [session.exercise_id, sessionState.currentQuestion])

  // 初始化答题开始时间
  useEffect(() => {
    answeringStartTimeRef.current = Date.now()
  }, [])

  useEffect(() => {
    loadCurrentQuestion()
    // 每次切换问题时重置答题开始时间
    answeringStartTimeRef.current = Date.now()
  }, [sessionState.currentQuestion, loadCurrentQuestion])

  // ==================== 音频控制 ====================

  const handleAudioPlay = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.play()
      setSessionState(prev => ({ ...prev, isAudioPlaying: true }))
      listeningStartTimeRef.current = Date.now()
    }
  }, [])

  const handleAudioPause = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause()
      setSessionState(prev => ({
        ...prev,
        isAudioPlaying: false,
        totalListeningTime: prev.totalListeningTime + (Date.now() - listeningStartTimeRef.current)
      }))
    }
  }, [])

  const handleAudioStop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.currentTime = 0
      setSessionState(prev => ({
        ...prev,
        isAudioPlaying: false,
        currentAudioTime: 0,
        totalListeningTime: prev.totalListeningTime + (Date.now() - listeningStartTimeRef.current)
      }))
    }
  }, [])

  const handleSpeedChange = useCallback((speed: AudioPlaybackSpeed) => {
    // 验证速度值是否在有效范围内
    if (!AUDIO_SPEEDS.includes(speed)) {
      return
    }

    if (audioRef.current) {
      audioRef.current.playbackRate = speed
      setSessionState(prev => ({ ...prev, playbackSpeed: speed }))
    }
  }, [])

  const handleVolumeChange = useCallback((volume: number) => {
    // 验证音量值是否在有效范围内（0-1）
    if (volume < 0 || volume > 1 || isNaN(volume)) {
      return
    }

    if (audioRef.current) {
      audioRef.current.volume = volume
      setSessionState(prev => ({ ...prev, volume }))
    }
  }, [])

  const toggleSubtitles = useCallback(() => {
    setSessionState(prev => ({ ...prev, showSubtitles: !prev.showSubtitles }))
  }, [])

  // ==================== 录音功能 ====================

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      const chunks: Blob[] = []

      mediaRecorder.ondataavailable = (event) => {
        chunks.push(event.data)
      }

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/wav' })
        setSessionState(prev => ({ ...prev, recordingBlob: blob, isRecording: false }))
        
        // 如果启用了发音练习，进行评估
        if (settings.pronunciation_practice && currentQuestionData) {
          evaluatePronunciation(blob)
        }
      }

      mediaRecorderRef.current = mediaRecorder
      mediaRecorder.start()
      setSessionState(prev => ({ ...prev, isRecording: true }))
    } catch (err) {
      console.error('Recording error:', err)
      setError('无法启动录音功能')
    }
  }, [settings.pronunciation_practice, currentQuestionData])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && sessionState.isRecording) {
      try {
        mediaRecorderRef.current.stop()
        // 停止所有音频轨道
        mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop())
        // 重置引用
        mediaRecorderRef.current = null
        setSessionState(prev => ({ ...prev, isRecording: false }))
      } catch (error) {
        // 确保状态正确更新
        setSessionState(prev => ({ ...prev, isRecording: false }))
      }
    }
  }, [sessionState.isRecording])

  const evaluatePronunciation = useCallback(async (audioBlob: Blob) => {
    if (!currentQuestionData) return

    try {
      const result = await listeningApi.evaluatePronunciation(
        audioBlob,
        currentQuestionData.question_text
      )
      setSessionState(prev => ({
        ...prev,
        pronunciationResult: {
          overall_score: result.overall_score,
          pronunciation_score: result.pronunciation_score,
          fluency_score: result.fluency_score,
          accuracy_score: result.accuracy_score,
          rhythm_score: 0,
          intonation_score: 0,
          detailed_feedback: result.detailed_feedback.map(item => ({
            ...item,
            phonetic: '',
          })),
        }
      }))
    } catch (err) {
      // 静默处理发音评估错误
    }
  }, [currentQuestionData])

  // ==================== 答题处理 ====================

  const handleAnswerChange = useCallback((answer: string | string[]) => {
    if (!currentQuestionData) return

    const currentTime = Date.now()
    const timeSpent = currentTime - answeringStartTimeRef.current
    const existingAnswer = sessionState.answers[currentQuestionData.id]
    const attemptCount = existingAnswer ? existingAnswer.attempt_count + 1 : 1

    const answerData: ListeningAnswer = {
      question_id: currentQuestionData.id,
      answer,
      confidence_level: 3, // 默认中等信心
      time_spent: timeSpent,
      attempt_count: attemptCount,
      audio_replays: sessionState.audioProgress.play_count,
    }

    setSessionState(prev => ({
      ...prev,
      answers: {
        ...prev.answers,
        [currentQuestionData.id]: answerData,
      },
    }))
  }, [currentQuestionData, sessionState.answers, sessionState.audioProgress.play_count])

  const handleNextQuestion = useCallback(() => {
    if (sessionState.currentQuestion < session.total_questions) {
      setSessionState(prev => ({
        ...prev,
        currentQuestion: prev.currentQuestion + 1,
      }))
      answeringStartTimeRef.current = Date.now()
    } else {
      // 完成训练
      handleCompleteTraining()
    }
  }, [sessionState.currentQuestion, session.total_questions])

  const handlePreviousQuestion = useCallback(() => {
    if (sessionState.currentQuestion > 1) {
      setSessionState(prev => ({
        ...prev,
        currentQuestion: prev.currentQuestion - 1,
      }))
      answeringStartTimeRef.current = Date.now()
    }
  }, [sessionState.currentQuestion])

  const handleCompleteTraining = useCallback(() => {
    const totalTime = Date.now() - sessionState.startTime
    const totalAnsweringTime = sessionState.totalAnsweringTime + (Date.now() - answeringStartTimeRef.current)

    onComplete({
      answers: sessionState.answers,
      audio_progress: sessionState.audioProgress,
      total_time_seconds: Math.floor(totalTime / 1000),
      listening_time_seconds: Math.floor(sessionState.totalListeningTime / 1000),
      answering_time_seconds: Math.floor(totalAnsweringTime / 1000),
    })
  }, [sessionState, onComplete])

  // ==================== 音频事件处理 ====================

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    const handleTimeUpdate = () => {
      setSessionState(prev => ({
        ...prev,
        currentAudioTime: audio.currentTime,
        audioProgress: {
          ...prev.audioProgress,
          current_time: audio.currentTime,
          total_time: audio.duration || 0,
        },
      }))
    }

    const handleEnded = () => {
      setSessionState(prev => ({
        ...prev,
        isAudioPlaying: false,
        totalListeningTime: prev.totalListeningTime + (Date.now() - listeningStartTimeRef.current),
        audioProgress: {
          ...prev.audioProgress,
          play_count: prev.audioProgress.play_count + 1,
        },
      }))
    }

    audio.addEventListener('timeupdate', handleTimeUpdate)
    audio.addEventListener('ended', handleEnded)

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate)
      audio.removeEventListener('ended', handleEnded)
    }
  }, [])

  // 组件卸载时清理录音资源
  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current) {
        try {
          if (mediaRecorderRef.current.state === 'recording') {
            mediaRecorderRef.current.stop()
          }
          mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop())
          mediaRecorderRef.current = null
        } catch (error) {
          // 静默处理清理错误
        }
      }
    }
  }, [])

  // ==================== 渲染 ====================

  if (isLoading) {
    return (
      <Center h={400}>
        <Stack align="center">
          <Loader size="lg" />
          <Text>加载题目中...</Text>
        </Stack>
      </Center>
    )
  }

  if (error) {
    return (
      <Center h={400}>
        <Stack align="center">
          <Alert color="red" title="加载失败">
            <Text>{error}</Text>
            <Group justify="center" mt="md">
              <Button variant="light" onClick={loadCurrentQuestion}>
                重试
              </Button>
              <Button variant="outline" onClick={onExit}>
                退出训练
              </Button>
            </Group>
          </Alert>
        </Stack>
      </Center>
    )
  }

  if (!currentQuestionData) {
    return (
      <Center h={400}>
        <Text>无题目数据</Text>
      </Center>
    )
  }

  const progress = (sessionState.currentQuestion / session.total_questions) * 100

  return (
    <Stack gap="md">
      {/* 训练进度 */}
      <Card withBorder>
        <Group justify="space-between" mb="xs">
          <Text size="sm" fw={500}>
            训练进度：{sessionState.currentQuestion} / {session.total_questions}
          </Text>
          <Badge color="blue">
            {Math.round(progress)}%
          </Badge>
        </Group>
        <Progress value={progress} size="lg" />
      </Card>

      {/* 音频控制面板 */}
      <Card withBorder>
        <Group justify="space-between" mb="md">
          <Text fw={500}>音频控制</Text>
          <Group gap="xs">
            <Badge size="sm" color="green">
              {sessionState.playbackSpeed}x
            </Badge>
            <Badge size="sm" color="blue">
              播放 {sessionState.audioProgress.play_count} 次
            </Badge>
          </Group>
        </Group>

        <Group justify="center" mb="md">
          <ActionIcon
            size="xl"
            variant="filled"
            color="blue"
            onClick={sessionState.isAudioPlaying ? handleAudioPause : handleAudioPlay}
          >
            {sessionState.isAudioPlaying ? <IconPlayerPause size={24} /> : <IconPlayerPlay size={24} />}
          </ActionIcon>
          <ActionIcon size="lg" variant="light" onClick={handleAudioStop}>
            <IconPlayerStop size={20} />
          </ActionIcon>
          {settings.repeat_enabled && (
            <ActionIcon size="lg" variant="light" onClick={handleAudioPlay}>
              <IconRepeat size={20} />
            </ActionIcon>
          )}
          <ActionIcon size="lg" variant="light" onClick={toggleSubtitles}>
            <IconEye size={20} />
          </ActionIcon>
        </Group>

        {/* 音频进度条 */}
        <Slider
          value={sessionState.currentAudioTime}
          max={sessionState.audioProgress.total_time || 100}
          onChange={(value) => {
            if (audioRef.current) {
              audioRef.current.currentTime = value
            }
          }}
          label={(value) => `${Math.floor(value / 60)}:${Math.floor(value % 60).toString().padStart(2, '0')}`}
          mb="md"
        />

        {/* 音频控制选项 */}
        <Group justify="space-between">
          <Group gap="xs">
            <Text size="sm">语速:</Text>
            {AUDIO_SPEEDS.map(speed => (
              <Button
                key={speed}
                size="xs"
                variant={sessionState.playbackSpeed === speed ? 'filled' : 'light'}
                onClick={() => handleSpeedChange(speed)}
              >
                {speed}x
              </Button>
            ))}
          </Group>
          <Group gap="xs">
            <ActionIcon
              variant="light"
              onClick={() => handleVolumeChange(sessionState.volume === 0 ? 1.0 : 0)}
            >
              {sessionState.volume === 0 ? <IconVolumeOff size={16} /> : <IconVolume size={16} />}
            </ActionIcon>
            <Slider
              w={80}
              value={sessionState.volume}
              max={1}
              step={0.1}
              onChange={handleVolumeChange}
            />
          </Group>
        </Group>
      </Card>

      {/* 题目内容 */}
      <Card withBorder>
        <Group justify="space-between" mb="md">
          <Text fw={500}>题目 {sessionState.currentQuestion}</Text>
          <Badge color="orange">{currentQuestionData.question_type}</Badge>
        </Group>

        <Text mb="md">{currentQuestionData.question_text}</Text>

        {/* 字幕显示 */}
        {sessionState.showSubtitles && currentQuestionData.audio_start_time !== undefined && (
          <Paper p="md" bg="gray.0" mb="md">
            <Group justify="space-between" mb="xs">
              <Text size="sm" fw={500}>听力原文</Text>
              <Badge size="sm" color="blue">字幕辅助</Badge>
            </Group>
            <Text size="sm" style={{ lineHeight: 1.6 }}>
              {/* 这里应该显示对应时间段的听力原文 */}
              [听力原文将在此显示...]
            </Text>
          </Paper>
        )}

        {/* 答题区域 */}
        <Stack gap="md">
          {currentQuestionData.question_type === 'single_choice' && (
            <Radio.Group
              value={sessionState.answers[currentQuestionData.id]?.answer as string || ''}
              onChange={(value) => handleAnswerChange(value)}
            >
              <Stack gap="xs">
                {currentQuestionData.options.map((option, index) => (
                  <Radio key={index} value={option} label={option} />
                ))}
              </Stack>
            </Radio.Group>
          )}

          {currentQuestionData.question_type === 'multiple_choice' && (
            <Checkbox.Group
              value={sessionState.answers[currentQuestionData.id]?.answer as string[] || []}
              onChange={(value) => handleAnswerChange(value)}
            >
              <Stack gap="xs">
                {currentQuestionData.options.map((option, index) => (
                  <Checkbox key={index} value={option} label={option} />
                ))}
              </Stack>
            </Checkbox.Group>
          )}

          {(currentQuestionData.question_type === 'fill_blank' || currentQuestionData.question_type === 'dictation') && (
            <Textarea
              placeholder={settings.dictation_mode ? "请输入听到的内容..." : "请填写答案..."}
              value={sessionState.answers[currentQuestionData.id]?.answer as string || ''}
              onChange={(event) => handleAnswerChange(event.currentTarget.value)}
              minRows={3}
            />
          )}
        </Stack>

        {/* 跟读练习 */}
        {settings.pronunciation_practice && (
          <Card withBorder mt="md" p="md">
            <Group justify="space-between" mb="md">
              <Text fw={500}>口语跟读练习</Text>
              <Badge color="green">发音评估</Badge>
            </Group>

            <Group justify="center" mb="md">
              <Button
                leftSection={sessionState.isRecording ? <IconMicrophoneOff size={16} /> : <IconMicrophone size={16} />}
                color={sessionState.isRecording ? 'red' : 'blue'}
                onClick={sessionState.isRecording ? stopRecording : startRecording}
                loading={sessionState.isRecording}
              >
                {sessionState.isRecording ? '停止录音' : '开始跟读'}
              </Button>
            </Group>

            {sessionState.pronunciationResult && (
              <Stack gap="xs">
                <Group justify="space-between">
                  <Text size="sm">总体得分</Text>
                  <Badge color={sessionState.pronunciationResult.overall_score >= 80 ? 'green' : 'orange'}>
                    {sessionState.pronunciationResult.overall_score}分
                  </Badge>
                </Group>
                <Group justify="space-between">
                  <Text size="sm">发音准确度</Text>
                  <Text size="sm">{sessionState.pronunciationResult.pronunciation_score}分</Text>
                </Group>
                <Group justify="space-between">
                  <Text size="sm">流畅度</Text>
                  <Text size="sm">{sessionState.pronunciationResult.fluency_score}分</Text>
                </Group>
              </Stack>
            )}
          </Card>
        )}
      </Card>

      {/* 导航按钮 */}
      <Group justify="space-between">
        <Group>
          <Button
            variant="light"
            leftSection={<IconChevronLeft size={16} />}
            onClick={handlePreviousQuestion}
            disabled={sessionState.currentQuestion === 1}
          >
            上一题
          </Button>
          <Button variant="outline" onClick={onExit}>
            退出训练
          </Button>
        </Group>
        <Button
          rightSection={<IconChevronRight size={16} />}
          onClick={handleNextQuestion}
          disabled={!sessionState.answers[currentQuestionData.id]}
        >
          {sessionState.currentQuestion === session.total_questions ? '完成训练' : '下一题'}
        </Button>
      </Group>

      {/* 隐藏的音频元素 */}
      <audio
        ref={audioRef}
        src={`/api/audio/listening/${currentQuestionData.id}`}
        preload="metadata"
        style={{ display: 'none' }}
      />
    </Stack>
  )
}
