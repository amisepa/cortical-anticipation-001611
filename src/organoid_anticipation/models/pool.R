# Three-level random-effects pooling with known sampling variances (spec v0.3 Section 6.5).
# Input CSV: rep, culture, experiment, yi, vi.  Output CSV: rep, est, se, df, ci_lo, ci_hi, ci90_lo, ci90_hi, p, sigma2_culture, sigma2_exp, converged
args <- commandArgs(trailingOnly = TRUE)
suppressPackageStartupMessages(library(metafor))
d <- read.csv(args[1])
out <- list()
for (r in unique(d$rep)) {
  x <- d[d$rep == r, ]
  fit <- tryCatch(rma.mv(yi, vi, random = ~ 1 | culture/experiment, data = x, method = "REML",
                         test = "t", dfs = "contain"), error = function(e) NULL)
  if (is.null(fit)) {
    out[[length(out) + 1]] <- data.frame(rep = r, est = NA, se = NA, df = NA, ci_lo = NA, ci_hi = NA,
                                         ci90_lo = NA, ci90_hi = NA, p = NA, sigma2_culture = NA, sigma2_exp = NA, converged = FALSE)
    next
  }
  df <- fit$ddf[[1]]
  q90 <- qt(0.95, df)
  out[[length(out) + 1]] <- data.frame(rep = r, est = fit$b[1], se = fit$se, df = df, ci_lo = fit$ci.lb, ci_hi = fit$ci.ub,
                                       ci90_lo = fit$b[1] - q90 * fit$se, ci90_hi = fit$b[1] + q90 * fit$se,
                                       p = fit$pval, sigma2_culture = fit$sigma2[1], sigma2_exp = fit$sigma2[2], converged = TRUE)
}
write.csv(do.call(rbind, out), args[2], row.names = FALSE)
