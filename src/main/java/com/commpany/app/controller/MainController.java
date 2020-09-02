package com.commpany.app.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.RequestMapping;

import com.commpany.app.service.BoardService;

public class MainController {

	@Autowired
	private BoardService boardService;

	@RequestMapping("test")
	public String test(Model model) {
	  model.addAttribute("viewAll", boardService.viewAll());
	  return "board/test";
	}

}
