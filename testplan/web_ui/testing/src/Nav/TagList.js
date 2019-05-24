import React, {Component} from 'react';
import PropTypes from 'prop-types';
import {Badge} from 'reactstrap';
import {StyleSheet, css} from 'aphrodite';


class TagList extends Component {

  render() {
    let tags = Object.assign({}, this.props.tags);

    const labels = [];
    if (tags.simple) {
      for (let tag of tags.simple) {
        labels.push(
          <Badge 
            key={this.props.entryName+tag} 
            className={css(styles.tags)}
            color='primary'>
            {tag}
          </Badge>
        );
      }
      delete tags.simple;
    }

    for (let tagKey in tags) {
      for (let tagValue in tags[tagKey]) {
        labels.push(
          <Badge 
            key={this.props.entryName+tagKey+tagValue} 
            className={css(styles.tags)} 
            color='primary'>
            {tagKey}={tagValue}
          </Badge>
        );
      }
    }

    return (
      <div className='tagList'>
        {labels}
      </div>
    );
  }
}

TagList.propTypes = {
  entryName: PropTypes.string,
  tags: PropTypes.object,
};

const styles = StyleSheet.create({
  tags: {
    'margin-right': '.4em',
  },
});

export default TagList;
