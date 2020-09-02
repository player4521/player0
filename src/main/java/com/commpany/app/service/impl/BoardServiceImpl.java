package com.commpany.app.service.impl;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.commpany.app.domain.BoardVO;
import com.commpany.app.mapper.BoardMapper;
import com.commpany.app.service.BoardService;

@Service
public class BoardServiceImpl implements BoardService {

	@Autowired
	private BoardMapper mapper;

	@Override
	public List<BoardVO> viewAll() {
		return mapper.viewAll();
	}

}