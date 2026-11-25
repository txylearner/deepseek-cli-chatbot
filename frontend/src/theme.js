/**
 * Naive UI 主题：把组件库的色板对齐到我们自己的设计变量。
 * 亮/暗两套共用同一组品牌色，只切换底色与文字色。
 */
const FONT =
  '"Inter", "PingFang SC", "Microsoft YaHei", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'

export function createThemeOverrides(isDark) {
  const text = isDark ? '#e8ecf7' : '#151a26'
  const text2 = isDark ? '#9aa3b8' : '#5b6478'
  const text3 = isDark ? '#6b7488' : '#8a93a6'
  const border = isDark ? 'rgba(255, 255, 255, 0.09)' : 'rgba(15, 23, 42, 0.09)'
  const card = isDark ? '#11141c' : '#ffffff'
  const body = isDark ? '#080a10' : '#f4f6fb'
  const soft = isDark ? '#161a24' : '#f1f3f9'

  return {
    common: {
      fontFamily: FONT,
      fontSize: '14px',
      borderRadius: '12px',
      borderRadiusSmall: '9px',
      primaryColor: '#7c5cff',
      primaryColorHover: '#9179ff',
      primaryColorPressed: '#6847e6',
      primaryColorSuppl: '#7c5cff',
      textColorBase: text,
      textColor1: text,
      textColor2: text2,
      textColor3: text3,
      bodyColor: body,
      cardColor: card,
      modalColor: card,
      popoverColor: card,
      inputColor: 'transparent',
      borderColor: border,
      dividerColor: border,
      hoverColor: soft,
      actionColor: soft,
    },
    Button: {
      fontWeight: '600',
      borderRadiusMedium: '10px',
      borderRadiusLarge: '12px',
    },
    Input: {
      color: 'transparent',
      colorFocus: 'transparent',
      border: '1px solid ' + border,
      borderHover: '1px solid rgba(124, 92, 255, 0.45)',
      borderFocus: '1px solid rgba(124, 92, 255, 0.65)',
      boxShadowFocus: '0 0 0 3px rgba(124, 92, 255, 0.16)',
    },
    Tag: {
      borderRadius: '999px',
    },
    Tooltip: {
      borderRadius: '8px',
    },
  }
}
