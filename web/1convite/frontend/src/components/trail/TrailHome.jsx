import React, { useState, useEffect, useRef, useMemo } from 'react';
import { TRAIL_CONFIG, TRAIL_DAYS_18M, TRAIL_DAYS_12M, TRAIL_ACTIONS } from '../../data/trailData';
import { playTrailClick, playTrailComplete, playTrailStreak, playTrailMilestone, playTrailCoin } from './trailSons';
import './TrailHome.css';

function formatDate(dateStr) {
  const d = new Date(dateStr);
  return d.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' });
}

function isYesterday(dateStr) {
  if (!dateStr) return false;
  const d = new Date(dateStr);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  return d.toDateString() === yesterday.toDateString();
}

function isToday(dateStr) {
  if (!dateStr) return false;
  return new Date(dateStr).toDateString() === new Date().toDateString();
}

export default function TrailHome({ onBack, userCoins, setUserCoins }) {
  const [duration, setDuration] = useState(() => localStorage.getItem('trail-duration') || '18m');
  const [currentDay, setCurrentDay] = useState(() => parseInt(localStorage.getItem('trail-current-day') || '1'));
  const [streak, setStreak] = useState(() => parseInt(localStorage.getItem('trail-streak') || '0'));
  const [lastDate, setLastDate] = useState(() => localStorage.getItem('trail-last-date') || '');
  const [completedDays, setCompletedDays] = useState(() => JSON.parse(localStorage.getItem('trail-completed') || '[]'));
  const [showMilestone, setShowMilestone] = useState(null);
  const [expandedDay, setExpandedDay] = useState(null);
  const listRef = useRef(null);

  const plan = duration === '12m' ? TRAIL_DAYS_12M : TRAIL_DAYS_18M;
  const totalDays = duration === '12m' ? 365 : 540;
  const dayData = plan[currentDay - 1];

  const currentMilestone = useMemo(() => {
    const key = duration === '12m' ? 'startDay12' : 'startDay18';
    let m = TRAIL_CONFIG.milestones[0];
    for (const ms of TRAIL_CONFIG.milestones) {
      if (currentDay >= ms[key]) m = ms;
      else break;
    }
    return m;
  }, [currentDay, duration]);

  useEffect(() => {
    if (listRef.current) {
      const el = listRef.current.querySelector('.trail-day-today');
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, []);

  const handleSelectDuration = (id) => {
    playTrailClick();
    setDuration(id);
    localStorage.setItem('trail-duration', id);
    setCurrentDay(1);
    localStorage.setItem('trail-current-day', '1');
    setStreak(0);
    localStorage.setItem('trail-streak', '0');
    setCompletedDays([]);
    localStorage.setItem('trail-completed', '[]');
    setLastDate('');
    localStorage.setItem('trail-last-date', '');
  };

  const handleCompleteDay = () => {
    if (completedDays.includes(currentDay)) return;
    playTrailComplete();

    const today = new Date().toDateString();
    const newCompleted = [...completedDays, currentDay];
    setCompletedDays(newCompleted);
    localStorage.setItem('trail-completed', JSON.stringify(newCompleted));

    // Streak logic
    let newStreak = streak;
    if (!isToday(lastDate)) {
      if (isYesterday(lastDate)) {
        newStreak = streak + 1;
      } else {
        newStreak = 1;
      }
      setStreak(newStreak);
      setLastDate(today);
      localStorage.setItem('trail-streak', newStreak);
      localStorage.setItem('trail-last-date', today);
    }

    // Coins
    setUserCoins(prev => {
      const val = prev + 10;
      localStorage.setItem('app-coins', val);
      return val;
    });
    playTrailCoin();

    // Streak milestone
    if (newStreak > 0 && newStreak % 7 === 0) {
      playTrailStreak();
    }

    // Check milestone
    const key = duration === '12m' ? 'startDay12' : 'startDay18';
    const milestone = TRAIL_CONFIG.milestones.find(m => m[key] === currentDay + 1);
    if (milestone) {
      setShowMilestone(milestone);
      playTrailMilestone();
      setTimeout(() => setShowMilestone(null), 3000);
    }

    // Advance day
    if (currentDay < totalDays) {
      const next = currentDay + 1;
      setCurrentDay(next);
      localStorage.setItem('trail-current-day', next);
    }
  };

  const handlePrevDay = () => {
    if (currentDay > 1) {
      playTrailClick();
      setCurrentDay(currentDay - 1);
      localStorage.setItem('trail-current-day', currentDay - 1);
    }
  };

  const handleNextDay = () => {
    if (currentDay < totalDays) {
      playTrailClick();
      setCurrentDay(currentDay + 1);
      localStorage.setItem('trail-current-day', currentDay + 1);
    }
  };

  const progressPct = Math.round((completedDays.length / totalDays) * 100);

  return (
    <div className="trail-container">
      {/* Header */}
      <div className="trail-header">
        <button onClick={() => { playTrailClick(); onBack(); }} className="trail-back-btn">←</button>
        <h2 className="trail-title">Trilha do Reino</h2>
      </div>

      {/* Stats */}
      <div className="trail-stats">
        <div className="trail-stat">
          <span className="trail-stat-icon">🔥</span>
          <span className="trail-stat-value">{streak}</span>
          <span className="trail-stat-label">dias seguidos</span>
        </div>
        <div className="trail-stat">
          <span className="trail-stat-icon">🪙</span>
          <span className="trail-stat-value">{userCoins}</span>
          <span className="trail-stat-label">Talentos</span>
        </div>
        <div className="trail-stat">
          <span className="trail-stat-icon">📖</span>
          <span className="trail-stat-value">{currentDay}</span>
          <span className="trail-stat-label">de {totalDays}</span>
        </div>
      </div>

      {/* Duration selector */}
      {!localStorage.getItem('trail-current-day') || currentDay === 1 ? (
        <div className="trail-duration-select">
          <p style={{ color: 'var(--text)', fontSize: 13, marginBottom: 8, textAlign: 'center' }}>
            Escolha a duração da sua jornada:
          </p>
          <div className="trail-duration-options">
            {TRAIL_CONFIG.durations.map(d => (
              <button
                key={d.id}
                onClick={() => handleSelectDuration(d.id)}
                className={`trail-duration-btn ${duration === d.id ? 'active' : ''}`}
              >
                {d.label}
              </button>
            ))}
          </div>
        </div>
      ) : null}

      {/* Progress bar */}
      <div className="trail-progress-bar">
        <div className="trail-progress-fill" style={{ width: `${progressPct}%` }} />
        <span className="trail-progress-text">{progressPct}% concluído</span>
      </div>

      {/* Current milestone badge */}
      <div className="trail-milestone-badge">
        <span>{currentMilestone.icon}</span>
        <span>{currentMilestone.name}</span>
      </div>

      {/* Day navigation */}
      {dayData && (
        <div className="trail-day-card">
          <div className="trail-day-nav">
            <button onClick={handlePrevDay} disabled={currentDay <= 1} className="trail-nav-btn">‹</button>
            <div className="trail-day-info">
              <span className="trail-day-label">Dia {currentDay}</span>
              <span className="trail-day-reading">{dayData.reading}</span>
            </div>
            <button onClick={handleNextDay} disabled={currentDay >= totalDays} className="trail-nav-btn">›</button>
          </div>

          {/* Devotional */}
          <div className="trail-devotional">
            <div className="trail-devotional-header">
              <span>🕯️</span> Reflexão do Dia
            </div>
            <p className="trail-devotional-text">{dayData.devotional}</p>
          </div>

          {/* Action */}
          <div className="trail-action">
            <div className="trail-action-header">
              <span>🤝</span> 1Convite Prático
            </div>
            <p className="trail-action-text">{dayData.action}</p>
          </div>

          {/* Complete button */}
          <button
            onClick={handleCompleteDay}
            className={`trail-complete-btn ${completedDays.includes(currentDay) ? 'completed' : ''}`}
            disabled={completedDays.includes(currentDay)}
          >
            {completedDays.includes(currentDay) ? '✅ Dia Concluído!' : '📖 Marcar como Lido (+10 🪙)'}
          </button>
        </div>
      )}

      {/* Trail map */}
      <div className="trail-map" ref={listRef}>
        <h3 className="trail-map-title">Mapa da Trilha</h3>
        {plan.slice(0, Math.min(currentDay + 10, totalDays)).map((day, idx) => {
          const dayNum = idx + 1;
          const isToday = dayNum === currentDay;
          const isCompleted = completedDays.includes(dayNum);
          const isPast = dayNum < currentDay;
          const milestone = TRAIL_CONFIG.milestones.find(m => {
            const key = duration === '12m' ? 'startDay12' : 'startDay18';
            return m[key] === dayNum;
          });

          return (
            <React.Fragment key={dayNum}>
              {milestone && (
                <div className="trail-map-milestone">
                  <span className="trail-map-milestone-icon">{milestone.icon}</span>
                  <span className="trail-map-milestone-name">{milestone.name}</span>
                </div>
              )}
              <div
                className={`trail-map-day ${isToday ? 'today' : ''} ${isCompleted ? 'completed' : ''} ${isPast ? 'past' : ''}`}
                onClick={() => { playTrailClick(); setExpandedDay(expandedDay === dayNum ? null : dayNum); }}
              >
                <div className="trail-map-day-dot">
                  {isCompleted ? '✓' : dayNum}
                </div>
                <div className="trail-map-day-info">
                  <span className="trail-map-day-reading">{day.reading}</span>
                  {isToday && <span className="trail-map-day-today-badge">HOJE</span>}
                </div>
              </div>
              {expandedDay === dayNum && (
                <div className="trail-map-day-expanded">
                  <p><strong>Reflexão:</strong> {day.devotional}</p>
                  <p><strong>Ação:</strong> {day.action}</p>
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Milestone popup */}
      {showMilestone && (
        <div className="trail-milestone-popup">
          <div className="trail-milestone-popup-content">
            <span className="trail-milestone-popup-icon">{showMilestone.icon}</span>
            <h3>Marco Alcançado!</h3>
            <p>{showMilestone.name}</p>
          </div>
        </div>
      )}
    </div>
  );
}
