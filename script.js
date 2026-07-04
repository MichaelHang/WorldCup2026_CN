// ========= Tab 切换 =========
function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(function(b) { b.classList.remove('active'); });
    document.querySelectorAll('.tab-content').forEach(function(c) { c.classList.remove('active'); });

    var map = { schedule: 0, groups: 1 };
    var btns = document.querySelectorAll('.tab-btn');
    if (map[tabName] !== undefined) btns[map[tabName]].classList.add('active');

    var content = document.getElementById('tab-' + tabName);
    if (content) content.classList.add('active');

    if (tabName === 'groups') {
        buildAllGroups();
    }
}


// ========= 赛程组装 =========
var STAGES = [
    {key:'group', title:'第一阶段小组赛', cls:'stage-group',
     dates:['0612','0613','0614','0615','0616','0617','0618','0619',
            '0620','0621','0622','0623','0624','0625','0626','0627','0628']},
    {key:'32', title:'Round of 32（1/16决赛）', cls:'stage-32',
     dates:['0629','0630','0701','0702','0703','0704']},
    {key:'16', title:'Round of 16（1/8决赛）', cls:'stage-16',
     dates:['0705','0706','0707','0708']},
    {key:'quarter', title:'Quarter-finals（1/4决赛）', cls:'stage-quarter',
     dates:['0715']},
    {key:'semi', title:'Semi-finals（半决赛）', cls:'stage-semi',
     dates:['0717']},
    {key:'final', title:'Final（总决赛）', cls:'stage-final',
     dates:['0719']}
];

function buildSchedule() {
    var container = document.getElementById('schedule-container');
    if (!container) return;
    var html = '';
    STAGES.forEach(function(stage) {
        html += '<div class="stage-card ' + stage.cls + '">';
        html += '<div class="stage-title">' + stage.title + '</div>';
        html += '<div class="table-wrapper">';
        stage.dates.forEach(function(d) {
            if (SCHEDULE_DATA[d]) html += SCHEDULE_DATA[d];
        });
        html += '</div></div>';
    });
    container.innerHTML = html;
}


// ======== 球队阵容数据 ========

var GROUP_TEAMS = {
    'A': ['墨西哥','南非','韩国','捷克'],
    'B': ['加拿大','波黑','卡塔尔','瑞士'],
    'C': ['巴西','摩洛哥','海地','苏格兰'],
    'D': ['美国','巴拉圭','澳大利亚','土耳其'],
    'E': ['德国','库拉索','科特迪瓦','厄瓜多尔'],
    'F': ['荷兰','日本','瑞典','突尼斯'],
    'G': ['比利时','埃及','伊朗','新西兰'],
    'H': ['西班牙','佛得角','沙特','乌拉圭'],
    'I': ['法国','塞内加尔','伊拉克','挪威'],
    'J': ['阿根廷','阿尔及利亚','奥地利','约旦'],
    'K': ['葡萄牙','刚果民主共和国','哥伦比亚','乌兹别克斯坦'],
    'L': ['英格兰','克罗地亚','加纳','巴拿马']
};

var TEAM_EN = {
    '墨西哥':'Mexico','南非':'South Africa','韩国':'South Korea','捷克':'Czech Republic',
    '加拿大':'Canada','波黑':'Bosnia and Herzegovina','卡塔尔':'Qatar','瑞士':'Switzerland',
    '巴西':'Brazil','摩洛哥':'Morocco','海地':'Haiti','苏格兰':'Scotland',
    '美国':'USA','巴拉圭':'Paraguay','澳大利亚':'Australia','土耳其':'Turkey',
    '德国':'Germany','库拉索':'Curacao','科特迪瓦':'Ivory Coast','厄瓜多尔':'Ecuador',
    '荷兰':'Netherlands','日本':'Japan','瑞典':'Sweden','突尼斯':'Tunisia',
    '比利时':'Belgium','埃及':'Egypt','伊朗':'Iran','新西兰':'New Zealand',
    '西班牙':'Spain','佛得角':'Cape Verde','沙特':'Saudi Arabia','乌拉圭':'Uruguay',
    '法国':'France','塞内加尔':'Senegal','伊拉克':'Iraq','挪威':'Norway',
    '阿根廷':'Argentina','阿尔及利亚':'Algeria','奥地利':'Austria','约旦':'Jordan',
    '葡萄牙':'Portugal','刚果民主共和国':'DR Congo','哥伦比亚':'Colombia','乌兹别克斯坦':'Uzbekistan',
    '英格兰':'England','克罗地亚':'Croatia','加纳':'Ghana','巴拿马':'Panama'
};

function parseScore(text) {
    if (!text || text === '\u2014') return null;
    var parts = text.trim().split(/[-:\uFF1A]/);
    if (parts.length !== 2) return null;
    var a = parseInt(parts[0]), b = parseInt(parts[1]);
    if (isNaN(a) || isNaN(b)) return null;
    return [a, b];
}

function calculateGroup(groupId) {
    var teams = GROUP_TEAMS[groupId];
    if (!teams) return [];
    var stats = {};
    teams.forEach(function(t) {
        stats[t] = { name:t, played:0, won:0, drawn:0, lost:0, gf:0, ga:0, pts:0 };
    });

    var rows = document.querySelectorAll('#tab-schedule .match-row');
    rows.forEach(function(row) {
        var groupEl = row.querySelector('.match-group');
        if (!groupEl) return;
        var groupText = groupEl.textContent.trim();
        var gMatch = groupText.match(/^([A-Z])/);
        if (!gMatch || gMatch[1] !== groupId) return;

        var teamEls = row.querySelectorAll('.match-team');
        var scoreEls = row.querySelectorAll('.match-score');
        if (teamEls.length < 2 || scoreEls.length < 2) return;

        var a = teamEls[0].textContent.trim();
        var b = teamEls[1].textContent.trim();
        var scoreA = scoreEls[0].textContent.trim();
        var scoreB = scoreEls[1].textContent.trim();

        var ga = parseInt(scoreA), gb = parseInt(scoreB);
        if (isNaN(ga) || isNaN(gb)) return;

        if (!stats[a] && stats[b]) {
            var tmp = a; a = b; b = tmp;
            tmp = ga; ga = gb; gb = tmp;
        }
        if (!stats[a] || !stats[b]) return;

        stats[a].played++; stats[b].played++;
        stats[a].gf += ga; stats[a].ga += gb;
        stats[b].gf += gb; stats[b].ga += ga;

        if (ga > gb)      { stats[a].won++; stats[a].pts += 3; stats[b].lost++; }
        else if (ga < gb) { stats[b].won++; stats[b].pts += 3; stats[a].lost++; }
        else              { stats[a].drawn++; stats[b].drawn++; stats[a].pts += 1; stats[b].pts += 1; }
    });

    var arr = Object.values(stats);
    arr.forEach(function(t) { t.gd = t.gf - t.ga; });
    arr.sort(function(a, b) {
        if (b.pts !== a.pts) return b.pts - a.pts;
        if (b.gd  !== a.gd)  return b.gd  - a.gd;
        if (b.gf  !== a.gf)  return b.gf  - a.gf;
        return a.name.localeCompare(b.name);
    });
    return arr;
}

function buildAllGroups() {
    var grid = document.getElementById('groupsGrid');
    var html = '';
    Object.keys(GROUP_TEAMS).forEach(function(g) {
        var standings = calculateGroup(g);
        html += '<div class="group-card">';
        html += '<h3>' + g + '\u7EC4</h3>';
        html += '<div class="table-wrapper"><table class="standings-table">';
        html += '<thead><tr><th>\u6392\u540D</th><th>\u7403\u961F</th><th>\u573A\u6B21</th><th>\u80DC</th><th>\u5E73</th><th>\u8D1F</th><th>\u8FDB</th><th>\u5931</th><th>\u51C0\u80DC</th><th>\u79EF\u5206</th></tr></thead>';
        html += '<tbody>';
        standings.forEach(function(t, i) {
            var rowClass = i < 2 ? ' class="qualify-row"' : '';
            html += '<tr' + rowClass + '>';
            html += '<td class="rank">' + (i+1) + '</td>';
            html += '<td><a href="teams/' + TEAM_EN[t.name] + '.html" class="team-clickable">' + t.name + '</a></td>';
            html += '<td>' + t.played + '</td>';
            html += '<td>' + t.won     + '</td>';
            html += '<td>' + t.drawn   + '</td>';
            html += '<td>' + t.lost    + '</td>';
            html += '<td>' + t.gf      + '</td>';
            html += '<td>' + t.ga      + '</td>';
            html += '<td>' + t.gd      + '</td>';
            html += '<td style="font-weight:700;color:#FFD700;">' + t.pts + '</td>';
            html += '</tr>';
        });
        html += '</tbody></table></div></div>';
    });
    grid.innerHTML = html;
}

// ========= 初始化 =========
function handleHash() {
    var hash = window.location.hash.replace('#', '') || 'schedule';
    if (['schedule', 'groups'].indexOf(hash) !== -1) {
        switchTab(hash);
    } else {
        switchTab('schedule');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    buildSchedule();
    handleHash();
});

window.addEventListener('hashchange', function() {
    handleHash();
});
