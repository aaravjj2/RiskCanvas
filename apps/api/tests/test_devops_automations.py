"""
Tests for DevOps automations (v2.5+).
"""
import pytest
from devops_automations import (
    GitLabMRBot,
    MonitorReporter,
    TestHarness,
    get_gitlab_mr_bot,
    get_monitor_reporter,
    get_test_harness
)


class TestGitLabMRBot:
    """Test GitLab MR bot functionality."""
    
    def test_analyze_simple_diff(self):
        """Test analyzing a simple diff."""
        bot = GitLabMRBot(demo_mode=True)
        
        diff = """
+++ a/test.py
@@ -1,3 +1,4 @@
 def test():
+    print("debug")
     return True
"""
        
        analysis = bot.analyze_changes(diff)
        
        assert "comments" in analysis
        assert "total_comments" in analysis
        assert analysis["total_comments"] >= 1  # Should detect print statement
    
    def test_analyze_diff_with_todo(self):
        """Test detecting TODO comments."""
        bot = GitLabMRBot(demo_mode=True)
        
        diff = "+# TODO: Fix this later"
        analysis = bot.analyze_changes(diff)
        
        assert analysis["total_comments"] >= 1
        assert any("TODO" in c["message"] for c in analysis["comments"])
    
    def test_analyze_diff_with_long_line(self):
        """Test detecting long lines."""
        bot = GitLabMRBot(demo_mode=True)
        
        long_line = "+" + ("x" * 250)  # 250 character line
        analysis = bot.analyze_changes(long_line)
        
        assert analysis["total_comments"] >= 1
        assert any("Long line" in c["message"] for c in analysis["comments"])
    
    def test_post_comment_demo_mode(self):
        """Test posting comments in demo mode."""
        bot = GitLabMRBot(demo_mode=True)
        
        result = bot.post_mr_comment(
            project_id="test_project",
            mr_iid=1,
            comment_body="Test comment"
        )
        
        assert result["success"] is True
        assert result["mode"] == "offline"
        assert "demo_comment" in result["comment_id"]
    
    def test_get_offline_comments(self):
        """Test retrieving offline comments."""
        bot = GitLabMRBot(demo_mode=True)
        
        bot.post_mr_comment("proj1", 1, "Comment 1")
        bot.post_mr_comment("proj1", 2, "Comment 2")
        
        comments = bot.get_offline_comments()
        
        assert len(comments) == 2
        assert comments[0]["body"] == "Comment 1"
        assert comments[1]["body"] == "Comment 2"


class TestMonitorReporter:
    """Test monitoring reporter functionality."""
    
    def test_check_api_health(self):
        """Test API health check."""
        reporter = MonitorReporter(demo_mode=True)
        
        health = reporter.check_api_health()
        
        assert "api_status" in health
        assert "database" in health
        assert "storage" in health
        assert "timestamp" in health
    
    def test_check_test_coverage(self):
        """Test coverage check."""
        reporter = MonitorReporter(demo_mode=True)
        
        coverage = reporter.check_test_coverage()
        
        assert "pytest_coverage" in coverage
        assert "e2e_tests" in coverage
        assert "timestamp" in coverage
    
    def test_generate_report_full(self):
        """Test generating full report."""
        reporter = MonitorReporter(demo_mode=True)
        
        report = reporter.generate_report(
            include_health=True,
            include_coverage=True
        )
        
        assert "report_id" in report
        assert "timestamp" in report
        assert "health" in report
        assert "coverage" in report
        assert report["demo_mode"] is True
    
    def test_generate_report_health_only(self):
        """Test generating health-only report."""
        reporter = MonitorReporter(demo_mode=True)
        
        report = reporter.generate_report(
            include_health=True,
            include_coverage=False
        )
        
        assert "health" in report
        assert "coverage" not in report
    
    def test_get_reports(self):
        """Test retrieving reports."""
        reporter = MonitorReporter(demo_mode=True)
        
        # Generate multiple reports
        reporter.generate_report()
        reporter.generate_report()
        reporter.generate_report()
        
        reports = reporter.get_reports(limit=2)
        
        assert len(reports) == 2  # Limited to 2
    
    def test_report_limit(self):
        """Test report retrieval limit."""
        reporter = MonitorReporter(demo_mode=True)
        
        # Generate 15 reports
        for _ in range(15):
            reporter.generate_report()
        
        reports = reporter.get_reports(limit=10)
        
        assert len(reports) == 10  # Should respect limit


class TestTestHarness:
    """Test offline test harness."""
    
    def test_simulate_mr_review(self):
        """Test MR review simulation."""
        harness = TestHarness()
        
        diff = "+console.log('debug')"
        result = harness.simulate_mr_review(diff)
        
        assert result["scenario"] == "mr_review"
        assert "analysis" in result
        assert "posted_comments" in result
        assert result["posted_comments"] >= 1
    
    def test_simulate_monitoring_cycle(self):
        """Test monitoring cycle simulation."""
        harness = TestHarness()
        
        result = harness.simulate_monitoring_cycle()
        
        assert result["scenario"] == "monitoring_cycle"
        assert "report" in result
        assert "health" in result["report"]
        assert "coverage" in result["report"]
    
    def test_run_scenario_mr_review(self):
        """Test running MR review scenario."""
        harness = TestHarness()
        
        result = harness.run_scenario(
            "mr_review",
            diff_text="+# TODO: implement"
        )
        
        assert result["scenario"] == "mr_review"
    
    def test_run_scenario_monitoring(self):
        """Test running monitoring scenario."""
        harness = TestHarness()
        
        result = harness.run_scenario("monitoring_cycle")
        
        assert result["scenario"] == "monitoring_cycle"
    
    def test_run_invalid_scenario(self):
        """Test running invalid scenario."""
        harness = TestHarness()
        
        with pytest.raises(ValueError, match="Unknown scenario type"):
            harness.run_scenario("invalid_scenario")
    
    def test_get_scenarios(self):
        """Test retrieving executed scenarios."""
        harness = TestHarness()
        
        harness.run_scenario("mr_review", diff_text="+test")
        harness.run_scenario("monitoring_cycle")
        
        scenarios = harness.get_scenarios()
        
        assert len(scenarios) == 2
        assert scenarios[0]["scenario"] == "mr_review"
        assert scenarios[1]["scenario"] == "monitoring_cycle"


class TestFactoryFunctions:
    """Test factory functions."""
    
    def test_get_gitlab_mr_bot(self):
        """Test getting GitLab MR bot."""
        bot = get_gitlab_mr_bot(demo_mode=True)
        
        assert isinstance(bot, GitLabMRBot)
        assert bot.demo_mode is True
    
    def test_get_monitor_reporter(self):
        """Test getting monitor reporter."""
        reporter = get_monitor_reporter(demo_mode=True)
        
        assert isinstance(reporter, MonitorReporter)
        assert reporter.demo_mode is True
    
    def test_get_test_harness(self):
        """Test getting test harness."""
        harness = get_test_harness()
        
        assert isinstance(harness, TestHarness)
