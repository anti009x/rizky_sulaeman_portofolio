module.exports = {
  content: [
    './templates/**/*.html',
    './static/**/*.js',
    './**/templates/**/*.html',  // For app-specific templates
    './**/static/**/*.js',       // For app-specific static files
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}